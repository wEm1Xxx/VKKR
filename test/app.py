"""
Веб-приложение турниров: Flask, Peewee, MySQL.

Содержит маршруты (главная, турнир, кабинет, пик/бан CS2, отчёты), генерацию сеток
single elimination / round robin и вспомогательную логику статусов матчей CS2.
"""

import os
import bcrypt

from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from Connection.Connection import connect

from Models.Roles import Roles
from Models.Users import Users
from Models.Teams import Teams
from Models.Team_members import Team_members
from Models.Tournaments import Tournaments
from Models.Tournament_registrations import Tournament_registrations
from Models.Matches import Matches
from Models.Match_results import Match_results
from Models.Cs2_pickban import Cs2_pickban
from Models.Match_map_score import Match_map_score

try:
    from Models.Team_join_requests import Team_join_requests
except ImportError:
    Team_join_requests = None

from Controllers.UsersController import UsersController


application = Flask(__name__, template_folder="templates", static_folder="static")
application.secret_key = os.getenv("SECRET_KEY", "super-secret-key")

login_manager = LoginManager(application)
login_manager.login_view = "login_page"
login_manager.login_message = "Пожалуйста, войдите в систему для доступа к этой странице."
login_manager.login_message_category = "warning"

# Карты для процедуры пик/бан (имена должны совпадать с тем, что пишется в БД)
CS2_MAP_POOL = ["Mirage", "Inferno", "Dust 2", "Nuke", "Ancient", "Overpass", "Anubis"]


@login_manager.user_loader
def user_loader(user_id):
    """Подгружает пользователя по id из cookie-сессии (интерфейс Flask-Login)."""
    return UsersController.show(int(user_id))


def init_db():
    """Создаёт таблицы, базовые роли и тестового admin1 при отсутствии."""
    db = connect()
    db.connect(reuse_if_open=True)

    tables = [
        Roles,
        Users,
        Teams,
        Team_members,
        Tournaments,
        Tournament_registrations,
        Matches,
        Match_results,
        Cs2_pickban,
        Match_map_score,
    ]
    if Team_join_requests is not None:
        tables.append(Team_join_requests)

    db.create_tables(tables, safe=True)

    roles_map = {
        1: "Администратор",
        2: "Капитан",
        3: "Игрок",
        4: "Зритель",
    }
    for rid, rname in roles_map.items():
        role = Roles.get_or_none(Roles.id == rid)
        if role is None:
            Roles.create(id=rid, name=rname)

    admin = Users.get_or_none(Users.username == "admin1")
    if admin is None:
        password_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
        Users.create(
            username="admin1",
            email="admin1@example.com",
            password_hash=password_hash,
            role_id=1,
        )

    db.close()


def is_cs2_name(game):
    """True, если строка game распознаётся как Counter-Strike 2 (разные написания)."""
    if game is None or not str(game).strip():
        return False
    g = str(game).strip().lower()
    compact = g.replace(" ", "").replace("-", "").replace(":", "")
    if compact in ("cs2", "counterstrike2"):
        return True
    return g in ("cs 2", "cs:2", "counter-strike 2", "counter strike 2")


def is_cs2_tournament(tournament):
    """True, если турнир помечен игрой CS2."""
    return tournament is not None and is_cs2_name(tournament.game)


def is_cs2_match(match):
    """True, если матч относится к турниру CS2 (по связанному tournament)."""
    try:
        t = match.tournament_id
        if isinstance(t, int):
            t = Tournaments.get_or_none(Tournaments.id == t)
        return is_cs2_tournament(t)
    except Exception:
        return False


def canonical_cs2_map(name):
    """Имя карты в том виде, как в CS2_MAP_POOL (устраняет расхождение регистра)."""
    if name is None:
        return None
    s = str(name).strip()
    if not s:
        return None
    low = s.lower()
    for m in CS2_MAP_POOL:
        if m.lower() == low:
            return m
    return None


def pickban_series_done(complete, order_maps):
    """BO3: 7 шагов и ровно 3 карты в серии (2 пика + decider)."""
    return complete and len(order_maps) == 3


def match_initial_status(tournament_id):
    """Стартовый статус нового матча: veto для CS2 (пик/бан), иначе pending."""
    t = Tournaments.get_or_none(Tournaments.id == tournament_id)
    return "veto" if is_cs2_tournament(t) else "pending"


def captain_team():
    """Команда, где текущий пользователь — капитан, или None."""
    return Teams.get_or_none(Teams.captain_id == current_user.id)


def generate_single_elimination(tournament_id, team_ids):
    """Строит олимпийскую сетку на вылет; пустые слоты — без команд, статус pending."""
    Matches.delete().where(Matches.tournament_id == tournament_id).execute()
    n = len(team_ids)
    if n < 2:
        return

    st = match_initial_status(tournament_id)

    target = 1
    while target < n:
        target *= 2
    padded = list(team_ids) + [None] * (target - n)
    pairs = [(padded[i], padded[i + 1]) for i in range(0, target, 2)]

    sizes = []
    x = target
    while x > 1:
        x //= 2
        sizes.append(x)

    for round_num, cnt in enumerate(sizes, start=1):
        for idx in range(cnt):
            if round_num == 1:
                t1, t2 = pairs[idx]
            else:
                t1, t2 = None, None
            Matches.create(
                tournament_id=tournament_id,
                round=round_num,
                team1_id=t1,
                team2_id=t2,
                status=st if (t1 and t2) else "pending",
            )


def generate_round_robin(tournament_id, team_ids):
    """Круговой турнир (circle method); нечётное число команд — фиктивный bye (None)."""
    Matches.delete().where(Matches.tournament_id == tournament_id).execute()
    teams = list(team_ids)
    if len(teams) < 2:
        return

    st = match_initial_status(tournament_id)

    if len(teams) % 2 == 1:
        teams.append(None)
    n = len(teams)
    for round_num in range(1, n):
        for i in range(n // 2):
            t1, t2 = teams[i], teams[n - 1 - i]
            if t1 is not None and t2 is not None:
                Matches.create(
                    tournament_id=tournament_id,
                    round=round_num,
                    team1_id=t1,
                    team2_id=t2,
                    status=st,
                )
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]


def generate_next_round(tournament_id):
    """Генерирует следующий раунд для single elimination турнира."""
    print("=" * 50)
    print(f"DEBUG: generate_next_round вызван для tournament_id={tournament_id}")

    tournament = Tournaments.get_or_none(Tournaments.id == tournament_id)
    if not tournament:
        print("DEBUG: Турнир не найден")
        return

    print(f"DEBUG: Турнир найден: {tournament.title}, формат={tournament.format}")

    if tournament.format != "single_elimination":
        print(f"DEBUG: Формат не single_elimination, а {tournament.format}")
        return

    # Получаем все матчи турнира
    all_matches = list(
        Matches.select()
        .where(Matches.tournament_id == tournament_id)
        .order_by(Matches.round, Matches.id)
    )

    if not all_matches:
        print("DEBUG: Нет матчей в турнире")
        return

    print(f"DEBUG: Всего матчей: {len(all_matches)}")
    for m in all_matches:
        print(f"  Матч #{m.id}: раунд={m.round}, статус={m.status}, winner_id={m.winner_id}")

    # Находим максимальный раунд
    max_round = max(m.round for m in all_matches)
    print(f"DEBUG: Максимальный раунд: {max_round}")

    # Получаем матчи последнего раунда
    last_round_matches = [m for m in all_matches if m.round == max_round]
    print(f"DEBUG: Матчей в последнем раунде: {len(last_round_matches)}")

    # Проверяем, все ли матчи последнего раунда завершены
    all_done = True
    for m in last_round_matches:
        print(f"  Матч #{m.id}: статус={m.status}")
        if m.status not in ("final", "confirmed"):
            print(f"    -> НЕ ЗАВЕРШЕН (статус {m.status})")
            all_done = False
        else:
            print(f"    -> ЗАВЕРШЕН")

    if not all_done:
        print("DEBUG: Не все матчи завершены, выходим")
        return

    print("DEBUG: Все матчи последнего раунда завершены!")

    # Если в последнем раунде только 1 матч - это финал
    if len(last_round_matches) == 1:
        print("DEBUG: Только 1 матч в последнем раунде - это финал")
        if last_round_matches[0].winner_id:
            print(f"DEBUG: Победитель финала: {last_round_matches[0].winner_id.name}")
            if tournament.status != "finished":
                Tournaments.update(status="finished").where(Tournaments.id == tournament_id).execute()
                print("DEBUG: Турнир завершен!")
        return

    # Создаем следующий раунд
    next_round = max_round + 1
    print(f"DEBUG: Создаем/обновляем раунд {next_round}")

    # Получаем существующие матчи следующего раунда
    existing_matches = list(
        Matches.select()
        .where(Matches.tournament_id == tournament_id, Matches.round == next_round)
        .order_by(Matches.id)
    )

    if existing_matches:
        print(f"DEBUG: Найдено {len(existing_matches)} существующих матчей в раунде {next_round}")

    # Пары для следующего раунда
    pairs = []
    for i in range(0, len(last_round_matches), 2):
        if i + 1 < len(last_round_matches):
            m1 = last_round_matches[i]
            m2 = last_round_matches[i + 1]
            print(f"  Пара: матч #{m1.id} (winner={m1.winner_id}) vs матч #{m2.id} (winner={m2.winner_id})")
            if m1.winner_id and m2.winner_id:
                pairs.append((m1.winner_id, m2.winner_id))
                print(f"    -> Матч: {m1.winner_id.name} vs {m2.winner_id.name}")
            else:
                pairs.append((None, None))
                print(f"    -> Нет победителей")
        else:
            m1 = last_round_matches[i]
            print(f"  Нечетное количество: матч #{m1.id} пропускает (bye)")
            pairs.append((m1.winner_id, None))
            if m1.winner_id:
                print(f"    -> {m1.winner_id.name} автоматически проходит дальше")

    # Обновляем или создаем матчи следующего раунда
    st = match_initial_status(tournament_id)
    updated_count = 0
    created_count = 0

    for idx, (t1, t2) in enumerate(pairs):
        if idx < len(existing_matches):
            # Обновляем существующий матч
            match = existing_matches[idx]
            if t1 or t2:
                match.team1_id = t1.id if t1 else None
                match.team2_id = t2.id if t2 else None
                match.status = st if (t1 and t2) else "pending"
                match.save()
                updated_count += 1
                print(f"  Обновлен матч #{match.id}: {t1.name if t1 else 'TBD'} vs {t2.name if t2 else 'TBD'}, статус={match.status}")
        else:
            # Создаем новый матч, если существующих не хватает
            if t1 or t2:
                new_match = Matches.create(
                    tournament_id=tournament_id,
                    round=next_round,
                    team1_id=t1.id if t1 else None,
                    team2_id=t2.id if t2 else None,
                    status=st if (t1 and t2) else "pending",
                )
                created_count += 1
                print(f"  Создан матч #{new_match.id}: {t1.name if t1 else 'TBD'} vs {t2.name if t2 else 'TBD'}, статус={new_match.status}")

    print(f"DEBUG: Обновлено {updated_count} матчей, создано {created_count} матчей для раунда {next_round}")
    print("=" * 50)


def captain_open_matches(team):
    """Матчи команды в статусе pending, турнир идёт, обе команды назначены (отчёт без CS2-карт)."""
    if not team:
        return []
    q = (
        Matches.select()
        .join(Tournaments, on=(Matches.tournament_id == Tournaments.id))
        .where(
            (Tournaments.status == "in_progress")
            & (Matches.status == "pending")
            & (Matches.team1_id.is_null(False))
            & (Matches.team2_id.is_null(False))
            & ((Matches.team1_id == team.id) | (Matches.team2_id == team.id))
        )
        .order_by(Matches.round, Matches.id)
    )
    return list(q)


def captain_veto_matches(team):
    """Матчи команды в фазе пик/бана CS2 (status veto)."""
    if not team:
        return []
    q = (
        Matches.select()
        .join(Tournaments, on=(Matches.tournament_id == Tournaments.id))
        .where(
            (Tournaments.status == "in_progress")
            & (Matches.status == "veto")
            & (Matches.team1_id.is_null(False))
            & (Matches.team2_id.is_null(False))
            & ((Matches.team1_id == team.id) | (Matches.team2_id == team.id))
        )
        .order_by(Matches.round, Matches.id)
    )
    return list(q)


def step_action(step):
    """Тип хода по номеру шага (1–6 ban/pick, 7 decider)."""
    if step in (1, 2, 5, 6):
        return "ban"
    if step in (3, 4):
        return "pick"
    if step == 7:
        return "decider"
    return None


def acting_team_for_step(match, step):
    """Какая команда ходит на шаге step (нечётные шаги — team1, чётные — team2)."""
    if step in (1, 3, 5):
        return match.team1_id
    if step in (2, 4, 6):
        return match.team2_id
    return None


def compute_pickban_state(match):
    """Снимок пик/бана: остаток пула, порядок карт серии, следующий шаг, завершённость, история."""
    rows = list(
        Cs2_pickban.select()
        .where(Cs2_pickban.match_id == match.id)
        .order_by(Cs2_pickban.step)
    )
    pool = set(CS2_MAP_POOL)
    order_maps = []
    for r in rows:
        canon = canonical_cs2_map(r.map_name)
        if canon and canon in pool:
            pool.discard(canon)
        if r.action == "pick" and canon:
            order_maps.append(canon)
        elif r.action == "decider" and canon:
            order_maps.append(canon)
    next_step = len(rows) + 1
    complete = len(rows) >= 7
    return pool, order_maps, next_step, complete, rows


def finalize_decider_if_needed(match):
    """После 6-го хода автоматически добавляет 7-й шаг (decider) и переводит матч в pending."""
    pool, _, next_step, complete, _ = compute_pickban_state(match)
    if complete:
        return
    if next_step != 7:
        return
    if len(pool) != 1:
        return
    dec = pool.pop()
    Cs2_pickban.create(
        match_id=match.id,
        step=7,
        action="decider",
        map_name=dec,
        team_id=None,
    )
    Matches.update(status="pending").where(Matches.id == match.id).execute()


def reconcile_cs2_match_status(match):
    """
    Чинит рассинхрон: статус pending без завершённого пик/бана или veto при уже готовой серии.
    Без этого капитан видит «завершите пик/бан» и одновременно «пик/бан уже завершён».
    """
    if not is_cs2_match(match) or not match.team1_id or not match.team2_id:
        return
    if match.status in ("finished", "confirmed", "appeal", "final"):
        return

    finalize_decider_if_needed(match)

    pool, order_maps, _, complete, _ = compute_pickban_state(match)
    done = pickban_series_done(complete, order_maps)

    if done:
        if match.status == "veto":
            Matches.update(status="pending").where(Matches.id == match.id).execute()
    else:
        if match.status == "pending":
            Matches.update(status="veto").where(Matches.id == match.id).execute()


@application.route("/", methods=["GET"])
def home():
    """Главная: список турниров."""
    tournaments = Tournaments.select().order_by(Tournaments.id.desc())
    return render_template("index.html", tournaments=tournaments)


@application.route("/tournament/<int:tournament_id>", methods=["GET"])
def tournament_detail(tournament_id):
    """Карточка турнира: команды, матчи, счёт, пик/бан CS2, авто-завершение турнира при чемпионе."""
    tournament = Tournaments.get_or_none(Tournaments.id == tournament_id)
    if not tournament:
        flash("Турнир не найден", "error")
        return redirect("/")

    participating = (
        Teams.select()
        .join(
            Tournament_registrations,
            on=(Teams.id == Tournament_registrations.team_id),
        )
        .where(Tournament_registrations.tournament_id == tournament_id)
        .order_by(Tournament_registrations.id)
    )

    matches = list(
        Matches.select()
        .where(Matches.tournament_id == tournament_id)
        .order_by(Matches.round, Matches.id)
    )

    for m in matches:
        if m.team1_id and m.team2_id and is_cs2_match(m):
            reconcile_cs2_match_status(m)
    matches = list(
        Matches.select()
        .where(Matches.tournament_id == tournament_id)
        .order_by(Matches.round, Matches.id)
    )

    scores = {}
    for m in matches:
        mr = (
            Match_results.select()
            .where(Match_results.match_id == m.id)
            .order_by(Match_results.id.desc())
            .first()
        )
        if mr:
            confirmed = mr.confirmed_by_id is not None
            try:
                if mr.confirmed_by is not None:
                    confirmed = True
            except Exception:
                pass
            scores[m.id] = {
                "s1": mr.score_team1,
                "s2": mr.score_team2,
                "confirmed": bool(confirmed),
            }

    pickban_by_match = {}
    map_scores_by_match = {}
    for m in matches:
        if is_cs2_match(m):
            _, order_maps, _, complete, hist = compute_pickban_state(m)
            pb_done = pickban_series_done(complete, order_maps)
            pickban_by_match[m.id] = {"done": pb_done, "order": order_maps, "history": hist}
            map_scores_by_match[m.id] = list(
                Match_map_score.select()
                .where(Match_map_score.match_id == m.id)
                .order_by(Match_map_score.map_order)
            )

    champion = None
    if matches:
        max_round = max(mm.round for mm in matches)
        for mm in matches:
            if mm.round == max_round and mm.status in ("final", "confirmed") and mm.winner_id:
                champion = mm.winner_id
                break

    if champion and tournament.status == "in_progress":
        Tournaments.update(status="finished").where(Tournaments.id == tournament.id).execute()
        tournament.status = "finished"

    return render_template(
        "tournament_detail.html",
        tournament=tournament,
        participating=participating,
        matches=matches,
        scores=scores,
        champion=champion,
        pickban_by_match=pickban_by_match,
        map_scores_by_match=map_scores_by_match,
        is_cs2_tournament=is_cs2_tournament(tournament),
    )


@application.route("/match/<int:match_id>/pickban", methods=["GET", "POST"])
@login_required
def match_pickban(match_id):
    """Страница пик/бана CS2; POST — ход капитана (шаги 1–6), decider создаётся автоматически."""
    match = Matches.get_or_none(Matches.id == match_id)
    if not match or not is_cs2_match(match):
        flash("Матч не найден или не CS2", "error")
        return redirect("/")

    reconcile_cs2_match_status(match)
    match = Matches.get_by_id(match.id)

    t1 = match.team1_id
    t2 = match.team2_id
    if not t1 or not t2:
        flash("Команды не назначены", "error")
        return redirect(url_for("tournament_detail", tournament_id=match.tournament_id.id))

    if match.status != "veto":
        _, order_maps, _, complete, _ = compute_pickban_state(match)
        if pickban_series_done(complete, order_maps):
            flash("Пик/бан завершён. Отправьте отчёт по картам из кабинета капитана.", "info")
        elif match.status in ("finished", "confirmed", "appeal", "final"):
            flash("Матч уже завершён.", "info")
        else:
            flash("Матч недоступен для пик/бана.", "error")
        return redirect(url_for("tournament_detail", tournament_id=match.tournament_id.id))

    pool, order_maps, next_step, complete, history = compute_pickban_state(match)

    acting_team = acting_team_for_step(match, next_step)
    my_team = captain_team()
    can_act = (
        my_team is not None
        and acting_team is not None
        and my_team.id == acting_team.id
        and current_user.role_id.id == 2
        and not complete
    )

    if request.method == "POST":
        if not can_act:
            flash("Сейчас не ваш ход", "error")
            return redirect(url_for("match_pickban", match_id=match.id))

        map_name = canonical_cs2_map(request.form.get("map_name"))
        if not map_name or map_name not in pool:
            flash("Некорректная карта", "error")
            return redirect(url_for("match_pickban", match_id=match.id))

        act = step_action(next_step)
        if act not in ("ban", "pick"):
            flash("Неверный шаг", "error")
            return redirect(url_for("match_pickban", match_id=match.id))

        Cs2_pickban.create(
            match_id=match.id,
            step=next_step,
            action=act,
            map_name=map_name,
            team_id=acting_team.id,
        )

        finalize_decider_if_needed(match)

        flash("Ход записан", "success")
        return redirect(url_for("match_pickban", match_id=match.id))

    finalize_decider_if_needed(match)
    pool, order_maps, next_step, complete, history = compute_pickban_state(match)
    acting_team = acting_team_for_step(match, next_step)
    can_act = (
        my_team is not None
        and acting_team is not None
        and my_team.id == acting_team.id
        and current_user.role_id.id == 2
        and not complete
    )

    return render_template(
        "match_pickban.html",
        match=match,
        pool=sorted(pool),
        history=history,
        order_maps=order_maps,
        next_step=next_step,
        complete=complete,
        acting_team=acting_team,
        can_act=can_act,
        step_action=step_action(next_step) if not complete else None,
        cs2_pool=CS2_MAP_POOL,
    )


@application.route("/match/<int:match_id>/report_cs2", methods=["GET", "POST"])
@login_required
def match_report_cs2(match_id):
    """Отчёт капитана по BO3: раунды на каждой карте, создание Match_results и map_scores."""
    match = Matches.get_or_none(Matches.id == match_id)
    if not match or not is_cs2_match(match):
        flash("Матч не найден или не CS2", "error")
        return redirect("/")

    reconcile_cs2_match_status(match)
    match = Matches.get_by_id(match.id)

    if match.status not in ("pending", "appeal"):
        flash("Матч недоступен для отчёта", "error")
        return redirect(url_for("tournament_detail", tournament_id=match.tournament_id.id))

    team = captain_team()
    if not team or current_user.role_id.id != 2:
        flash("Только капитан", "error")
        return redirect("/dashboard")

    if match.team1_id.id != team.id and match.team2_id.id != team.id:
        flash("Это не ваш матч", "error")
        return redirect("/dashboard")

    _, order_maps, _, complete, _ = compute_pickban_state(match)
    if not pickban_series_done(complete, order_maps):
        flash("Сначала завершите пик/бан (7 шагов, три карты в серии).", "error")
        return redirect(url_for("match_pickban", match_id=match.id))

    if Match_results.get_or_none(Match_results.match_id == match.id):
        flash("Счёт уже отправлен", "error")
        return redirect("/dashboard")

    t1 = match.team1_id
    t2 = match.team2_id

    if request.method == "POST":
        score_rows = []
        for i, mn in enumerate(order_maps, start=1):
            a = request.form.get(f"r1_{i}")
            b = request.form.get(f"r2_{i}")

            # Пропускаем пустые поля (позволяем не заполнять третью карту)
            if a == "" or b == "" or a is None or b is None:
                continue

            try:
                a = int(a)
                b = int(b)
            except (TypeError, ValueError):
                flash("Введите целые числа для всех карт", "error")
                return redirect(url_for("match_report_cs2", match_id=match.id))

            if a < 0 or b < 0:
                flash("Счёт не может быть отрицательным", "error")
                return redirect(url_for("match_report_cs2", match_id=match.id))

            if a == b:
                flash("Ничья на карте недопустима", "error")
                return redirect(url_for("match_report_cs2", match_id=match.id))

            score_rows.append((mn, a, b, i))

        if not score_rows:
            flash("Заполните хотя бы одну карту", "error")
            return redirect(url_for("match_report_cs2", match_id=match.id))

        w1 = w2 = 0
        for mn, a, b, _ord in score_rows:
            if a > b:
                w1 += 1
            else:
                w2 += 1

        # Логика проверки для BO3
        if w1 == 1 and w2 == 1:
            # При счете 1:1 нужно 3 карты
            if len(score_rows) < 3:
                flash("При счете 1:1 нужно заполнить все три карты", "error")
                return redirect(url_for("match_report_cs2", match_id=match.id))
            # Если 3 карты, проверяем победу
            if max(w1, w2) < 2:
                flash("При счете 1:1 нужна победа 2-1", "error")
                return redirect(url_for("match_report_cs2", match_id=match.id))
        elif w1 == 2 or w2 == 2:
            # Счет 2:0 - победа, третью карту не требуем
            pass
        else:
            flash("Некорректный счет серии", "error")
            return redirect(url_for("match_report_cs2", match_id=match.id))

        winner = t1 if w1 > w2 else t2

        # Очищаем старые записи карт
        Match_map_score.delete().where(Match_map_score.match_id == match.id).execute()
        for mn, a, b, ord_i in score_rows:
            Match_map_score.create(
                match_id=match.id,
                map_name=mn,
                team1_rounds=a,
                team2_rounds=b,
                map_order=ord_i,
            )

        Match_results.create(
            match_id=match.id,
            score_team1=w1,
            score_team2=w2,
            reported_by=current_user.id,
        )
        Matches.update(winner_id=winner.id, status="finished").where(Matches.id == match.id).execute()

        flash("Серия отправлена администратору", "success")
        return redirect("/dashboard")

    return render_template(
        "match_report_cs2.html",
        match=match,
        order_maps=order_maps,
        team1=t1,
        team2=t2,
    )


@application.route("/login", methods=["GET", "POST"])
def login_page():
    """Форма входа (email или username + пароль)."""
    message = ""
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")

        if UsersController.auth(login, password):
            user = UsersController.show_login(login)
            login_user(user)
            return redirect("/dashboard")

        message = "Неверный логин или пароль"

    return render_template("login.html", message=message)


@application.route("/register", methods=["GET", "POST"])
def register_page():
    """Регистрация с выбором роли (капитан / игрок / зритель)."""
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        role_id = int(request.form.get("role_id", "4"))

        if role_id not in (2, 3, 4):
            role_id = 4

        if not all([username, email, password, password2]):
            message = "Заполните все поля"
            return render_template("register.html", message=message)

        if password != password2:
            message = "Пароли не совпадают"
            return render_template("register.html", message=message)

        if Users.get_or_none(Users.username == username):
            message = "Пользователь с таким username уже существует"
            return render_template("register.html", message=message)

        if Users.get_or_none(Users.email == email):
            message = "Пользователь с таким email уже существует"
            return render_template("register.html", message=message)

        created = UsersController.add(
            username=username,
            email=email,
            password=password,
            role_id=role_id
        )
        if created:
            return redirect("/login")

        message = "Ошибка регистрации"

    return render_template("register.html", message=message)


@application.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Личный кабинет в зависимости от роли: админ, капитан, игрок, зритель."""
    tournaments = Tournaments.select().order_by(Tournaments.id.desc())

    # Для админа - неподтвержденные результаты с картами
    unconfirmed = list(
        Match_results.select()
        .where(Match_results.confirmed_by.is_null(True))
        .order_by(Match_results.id.desc())
    )

    # Апелляции для админа
    appeals = list(
        Match_results.select()
        .where(Match_results.appealed_by.is_null(False))
        .order_by(Match_results.id.desc())
    )

    # Получаем счёт по картам для каждого матча (для админа)
    map_scores_by_match = {}

    # Для неподтвержденных
    for result in unconfirmed:
        match_id = result.match_id.id
        map_scores = list(
            Match_map_score.select()
            .where(Match_map_score.match_id == match_id)
            .order_by(Match_map_score.map_order)
        )
        if map_scores:
            map_scores_by_match[match_id] = map_scores

    # Для апелляций
    for result in appeals:
        match_id = result.match_id.id
        map_scores = list(
            Match_map_score.select()
            .where(Match_map_score.match_id == match_id)
            .order_by(Match_map_score.map_order)
        )
        if map_scores:
            map_scores_by_match[match_id] = map_scores

    # Получаем всех пользователей для админа
    users = list(Users.select().order_by(Users.id))

    # Для капитана
    my_team = None
    my_members = []
    pending_join_requests = []
    registered_tournaments = []
    captain_matches = []
    veto_matches = []
    confirmed_matches = []

    # Для игрока
    player_team = None
    player_team_members = []

    if current_user.role_id.id == 2:
        my_team = captain_team()
        if my_team:
            my_members = list(
                Team_members.select()
                .where(Team_members.team_id == my_team.id)
                .order_by(Team_members.id)
            )
            captain_matches = captain_open_matches(my_team)
            veto_matches = captain_veto_matches(my_team)

            confirmed_matches = list(
                Matches.select()
                .join(Tournaments, on=(Matches.tournament_id == Tournaments.id))
                .where(
                    (Tournaments.status == "in_progress") &
                    (Matches.status == "confirmed") &
                    ((Matches.team1_id == my_team.id) | (Matches.team2_id == my_team.id))
                )
                .order_by(Matches.round, Matches.id)
            )

            if Team_join_requests is not None:
                pending_join_requests = list(
                    Team_join_requests.select()
                    .where(
                        (Team_join_requests.team_id == my_team.id) &
                        (Team_join_requests.status == "pending")
                    )
                    .order_by(Team_join_requests.id.desc())
                )
            registered_tournaments = list(
                Tournaments.select()
                .join(
                    Tournament_registrations,
                    on=(Tournaments.id == Tournament_registrations.tournament_id),
                )
                .where(Tournament_registrations.team_id == my_team.id)
                .order_by(Tournaments.id.desc())
            )

    if current_user.role_id.id == 3:
        membership = Team_members.get_or_none(Team_members.user_id == current_user.id)
        if membership:
            player_team = membership.team_id
            player_team_members = list(
                Team_members.select()
                .where(Team_members.team_id == player_team.id)
                .order_by(Team_members.id)
            )

    return render_template(
        "dashboard.html",
        user=current_user,
        tournaments=tournaments,
        unconfirmed=unconfirmed,
        appeals=appeals,
        map_scores_by_match=map_scores_by_match,
        users=users,
        my_team=my_team,
        my_members=my_members,
        pending_join_requests=pending_join_requests,
        registered_tournaments=registered_tournaments,
        player_team=player_team,
        player_team_members=player_team_members,
        captain_matches=captain_matches,
        veto_matches=veto_matches,
        confirmed_matches=confirmed_matches,
    )


@application.route("/captain/match/report", methods=["POST"])
@login_required
def captain_report_match():
    """Отправка счёта по матчу не-CS2 (один счёт за матч); для CS2 редирект на отчёт по картам."""
    if current_user.role_id.id != 2:
        return redirect("/logout")

    team = captain_team()
    match_id = request.form.get("match_id")
    s1 = request.form.get("score1")
    s2 = request.form.get("score2")

    if not team or not match_id or s1 is None or s2 is None:
        flash("Заполните все поля", "error")
        return redirect("/dashboard")

    try:
        s1 = int(s1)
        s2 = int(s2)
    except ValueError:
        flash("Некорректный счёт", "error")
        return redirect("/dashboard")

    if s1 == s2:
        flash("Ничья недопустима", "error")
        return redirect("/dashboard")

    m = Matches.get_or_none(Matches.id == int(match_id))
    if not m or m.status not in ("pending", "appeal"):
        flash("Матч недоступен", "error")
        return redirect("/dashboard")

    if is_cs2_match(m):
        flash("Для CS2 используйте отчёт по картам", "info")
        return redirect(url_for("match_report_cs2", match_id=m.id))

    if not m.team1_id or not m.team2_id:
        flash("Матч ещё не готов", "error")
        return redirect("/dashboard")

    t1_id = m.team1_id.id
    t2_id = m.team2_id.id
    if team.id not in (t1_id, t2_id):
        flash("Это не матч вашей команды", "error")
        return redirect("/dashboard")

    if Match_results.get_or_none(Match_results.match_id == m.id):
        flash("Счёт по этому матчу уже отправлен", "error")
        return redirect("/dashboard")

    winner_id = t1_id if s1 > s2 else t2_id

    Match_results.create(
        match_id=m.id,
        score_team1=s1,
        score_team2=s2,
        reported_by=current_user.id,
    )
    Matches.update(winner_id=winner_id, status="finished").where(Matches.id == m.id).execute()
    flash("Счёт отправлен администратору на подтверждение", "success")
    return redirect("/dashboard")


@application.route("/captain/confirm_match", methods=["POST"])
@login_required
def captain_confirm_match():
    """Капитан подтверждает согласие с результатом матча."""
    if current_user.role_id.id != 2:
        flash("Доступ запрещен", "error")
        return redirect("/dashboard")

    team = captain_team()
    if not team:
        flash("Вы не являетесь капитаном команды", "error")
        return redirect("/dashboard")

    match_id = request.form.get("match_id")
    if not match_id:
        flash("Матч не выбран", "error")
        return redirect("/dashboard")

    match = Matches.get_or_none(Matches.id == int(match_id))
    if not match:
        flash("Матч не найден", "error")
        return redirect("/dashboard")

    # Проверяем, что команда капитана участвует в этом матче
    if match.team1_id.id != team.id and match.team2_id.id != team.id:
        flash("Это не ваш матч", "error")
        return redirect("/dashboard")

    result = Match_results.get_or_none(Match_results.match_id == match.id)
    if not result:
        flash("Результат не найден", "error")
        return redirect("/dashboard")

    # Проверяем, что результат подтвержден админом
    if not result.confirmed_by_id:
        flash("Результат еще не подтвержден администратором", "error")
        return redirect("/dashboard")

    # Проверяем, не подана ли уже апелляция
    if result.appealed_by_id:
        flash("Апелляция уже подана", "error")
        return redirect("/dashboard")

    # Сохраняем согласие команды и проверяем, согласны ли обе
    both_agreed = False
    if match.team1_id.id == team.id:
        Match_results.update(
            agreed_by_team1=True
        ).where(Match_results.id == result.id).execute()

        # Проверяем, согласна ли вторая команда
        updated_result = Match_results.get_by_id(result.id)
        if updated_result.agreed_by_team1 and updated_result.agreed_by_team2:
            both_agreed = True
            flash("Обе команды согласны с результатом! Матч окончательно завершен.", "success")
        else:
            flash("Ваша команда согласна с результатом. Ожидаем согласия второй команды.", "info")

    elif match.team2_id.id == team.id:
        Match_results.update(
            agreed_by_team2=True
        ).where(Match_results.id == result.id).execute()

        # Проверяем, согласна ли вторая команда
        updated_result = Match_results.get_by_id(result.id)
        if updated_result.agreed_by_team1 and updated_result.agreed_by_team2:
            both_agreed = True
            flash("Обе команды согласны с результатом! Матч окончательно завершен.", "success")
        else:
            flash("Ваша команда согласна с результатом. Ожидаем согласия второй команды.", "info")

    # Если обе команды согласны - переводим матч в финальный статус
    if both_agreed:
        Matches.update(status="final").where(Matches.id == match.id).execute()

        # Генерируем следующий раунд
        generate_next_round(match.tournament_id.id)

        # Обновляем турнир - проверяем, не закончился ли он
        tournament = match.tournament_id
        all_final = True
        for m in Matches.select().where(Matches.tournament_id == tournament.id):
            if m.status not in ("final", "confirmed"):
                all_final = False
                break
        if all_final:
            Tournaments.update(status="finished").where(Tournaments.id == tournament.id).execute()

    return redirect("/dashboard")


@application.route("/admin/tournament/start", methods=["POST"])
@login_required
def admin_start_tournament():
    """Админ запускает турнир из registration: генерирует матчи и ставит статус in_progress."""
    if current_user.role_id.id != 1:
        return redirect("/logout")

    tournament_id = request.form.get("tournament_id")
    if not tournament_id:
        flash("Турнир не выбран", "error")
        return redirect("/dashboard")

    tournament = Tournaments.get_or_none(Tournaments.id == int(tournament_id))
    if not tournament:
        flash("Турнир не найден", "error")
        return redirect("/dashboard")

    if tournament.status != "registration":
        flash("Турнир нельзя запустить в текущем статусе", "error")
        return redirect("/dashboard")

    regs = list(
        Tournament_registrations.select().where(
            Tournament_registrations.tournament_id == tournament.id
        )
    )
    team_ids = [r.team_id.id for r in regs]

    if len(team_ids) < 2:
        flash("Для старта нужно минимум 2 зарегистрированные команды", "error")
        return redirect("/dashboard")

    fmt = (tournament.format or "").strip()
    if fmt == "single_elimination":
        generate_single_elimination(tournament.id, team_ids)
    elif fmt == "round_robin":
        generate_round_robin(tournament.id, team_ids)
    else:
        flash("Неизвестный формат турнира", "error")
        return redirect("/dashboard")

    Tournaments.update(status="in_progress").where(Tournaments.id == tournament.id).execute()
    flash("Турнир запущен, сетка сгенерирована", "success")
    return redirect("/dashboard")


@application.route("/captain/team/create", methods=["POST"])
@login_required
def captain_create_team():
    """Капитан создаёт команду и сам попадает в состав."""
    if current_user.role_id.id != 2:
        return redirect("/logout")

    name = request.form.get("name", "").strip()
    if not name:
        flash("Введите название команды", "error")
        return redirect("/dashboard")

    if captain_team():
        flash("У вас уже есть команда", "error")
        return redirect("/dashboard")

    team = Teams.create(name=name, captain_id=current_user.id)
    Team_members.create(team_id=team.id, user_id=current_user.id)
    flash("Команда создана", "success")
    return redirect("/dashboard")


@application.route("/captain/team/remove_player", methods=["POST"])
@login_required
def captain_remove_player():
    """Капитан исключает игрока из своей команды (не себя)."""
    if current_user.role_id.id != 2:
        return redirect("/logout")

    team = captain_team()
    user_id = request.form.get("user_id")

    if not team or not user_id:
        flash("Некорректные данные", "error")
        return redirect("/dashboard")

    if int(user_id) == current_user.id:
        flash("Нельзя удалить капитана из команды", "error")
        return redirect("/dashboard")

    Team_members.delete().where(
        (Team_members.team_id == team.id) & (Team_members.user_id == int(user_id))
    ).execute()
    flash("Игрок исключён из команды", "success")
    return redirect("/dashboard")


@application.route("/captain/join_request/approve", methods=["POST"])
@login_required
def captain_approve_join():
    """Капитан одобряет заявку игрока в команду."""
    if current_user.role_id.id != 2 or Team_join_requests is None:
        return redirect("/logout")

    team = captain_team()
    req_id = request.form.get("request_id")
    if not team or not req_id:
        flash("Ошибка запроса", "error")
        return redirect("/dashboard")

    jr = Team_join_requests.get_or_none(
        (Team_join_requests.id == int(req_id)) &
        (Team_join_requests.team_id == team.id) &
        (Team_join_requests.status == "pending")
    )
    if not jr:
        flash("Заявка не найдена", "error")
        return redirect("/dashboard")

    exists = Team_members.get_or_none(
        (Team_members.team_id == team.id) & (Team_members.user_id == jr.player_id.id)
    )
    if not exists:
        Team_members.create(team_id=team.id, user_id=jr.player_id.id)

    Team_join_requests.update(status="approved").where(Team_join_requests.id == jr.id).execute()
    flash("Игрок принят в команду", "success")
    return redirect("/dashboard")


@application.route("/captain/join_request/reject", methods=["POST"])
@login_required
def captain_reject_join():
    """Капитан отклоняет заявку игрока."""
    if current_user.role_id.id != 2 or Team_join_requests is None:
        return redirect("/logout")

    team = captain_team()
    req_id = request.form.get("request_id")
    if not team or not req_id:
        flash("Ошибка запроса", "error")
        return redirect("/dashboard")

    updated = Team_join_requests.update(status="rejected").where(
        (Team_join_requests.id == int(req_id)) &
        (Team_join_requests.team_id == team.id) &
        (Team_join_requests.status == "pending")
    ).execute()

    if updated:
        flash("Заявка отклонена", "success")
    else:
        flash("Заявка не найдена", "error")
    return redirect("/dashboard")


@application.route("/captain/tournament/register", methods=["POST"])
@login_required
def captain_register_tournament():
    """Регистрирует команду капитана на турнир (пока открыта регистрация и есть слоты)."""
    if current_user.role_id.id != 2:
        return redirect("/logout")

    team = captain_team()
    tournament_id = request.form.get("tournament_id")

    if not team:
        flash("Сначала создайте команду", "error")
        return redirect("/dashboard")

    if not tournament_id:
        flash("Выберите турнир", "error")
        return redirect("/dashboard")

    tournament = Tournaments.get_or_none(Tournaments.id == int(tournament_id))
    if not tournament:
        flash("Турнир не найден", "error")
        return redirect("/dashboard")

    if tournament.status != "registration":
        flash("Регистрация на этот турнир закрыта", "error")
        return redirect("/dashboard")

    regs = Tournament_registrations.select().where(
        Tournament_registrations.tournament_id == tournament.id
    ).count()
    if regs >= tournament.max_teams:
        flash("Турнир заполнен", "error")
        return redirect("/dashboard")

    dup = Tournament_registrations.get_or_none(
        (Tournament_registrations.tournament_id == tournament.id) &
        (Tournament_registrations.team_id == team.id)
    )
    if dup:
        flash("Команда уже зарегистрирована", "error")
        return redirect("/dashboard")

    Tournament_registrations.create(tournament_id=tournament.id, team_id=team.id)
    flash("Команда зарегистрирована на турнир", "success")
    return redirect("/dashboard")


@application.route("/player/teams", methods=["GET"])
@login_required
def player_teams():
    """Игрок: список команд для подачи заявки на вступление."""
    if current_user.role_id.id != 3:
        return redirect("/logout")

    teams = Teams.select().order_by(Teams.name)
    sent_team_ids = set()
    if Team_join_requests is not None:
        sent_team_ids = {
            r.team_id.id
            for r in Team_join_requests.select().where(Team_join_requests.player_id == current_user.id)
        }

    membership = Team_members.get_or_none(Team_members.user_id == current_user.id)
    my_team_id = membership.team_id.id if membership else None

    return render_template(
        "player_teams.html",
        teams=teams,
        sent_team_ids=sent_team_ids,
        my_team_id=my_team_id,
    )


@application.route("/player/team/request", methods=["POST"])
@login_required
def player_team_request():
    """Игрок отправляет заявку в выбранную команду."""
    if current_user.role_id.id != 3 or Team_join_requests is None:
        return redirect("/logout")

    team_id = request.form.get("team_id")
    if not team_id:
        flash("Команда не выбрана", "error")
        return redirect("/player/teams")

    team = Teams.get_or_none(Teams.id == int(team_id))
    if not team:
        flash("Команда не найдена", "error")
        return redirect("/player/teams")

    if Team_members.get_or_none(
        (Team_members.team_id == team.id) & (Team_members.user_id == current_user.id)
    ):
        flash("Вы уже в этой команде", "error")
        return redirect("/player/teams")

    if Team_join_requests.get_or_none(
        (Team_join_requests.team_id == team.id) & (Team_join_requests.player_id == current_user.id)
    ):
        flash("Запрос уже отправлен", "error")
        return redirect("/player/teams")

    Team_join_requests.create(team_id=team.id, player_id=current_user.id, status="pending")
    flash("Запрос отправлен капитану", "success")
    return redirect("/player/teams")


@application.route("/create_tournament", methods=["POST"])
@login_required
def create_tournament():
    """Админ создаёт турнир со статусом registration."""
    if current_user.role_id.id != 1:
        return redirect("/logout")

    title = request.form.get("title", "").strip()
    game = request.form.get("game", "").strip()
    fmt = request.form.get("format", "").strip()
    max_teams = request.form.get("max_teams", "").strip()
    start_date = request.form.get("start_date", "").strip()

    if not all([title, game, fmt, max_teams, start_date]):
        flash("Заполните все поля турнира", "error")
        return redirect("/dashboard")

    if fmt not in ("single_elimination", "round_robin"):
        flash("Неверный формат турнира", "error")
        return redirect("/dashboard")

    try:
        Tournaments.create(
            title=title,
            game=game,
            format=fmt,
            max_teams=int(max_teams),
            start_date=start_date.replace("T", " "),
            status="registration",
            created_by=current_user.id,
        )
        flash("Турнир успешно создан", "success")
    except Exception as e:
        flash(f"Ошибка создания турнира: {str(e)}", "error")

    return redirect("/dashboard")


@application.route("/finish_tournament", methods=["POST"])
@login_required
def finish_tournament():
    """Админ принудительно переводит турнир в статус finished."""
    if current_user.role_id.id != 1:
        return redirect("/logout")

    tournament_id = request.form.get("tournament_id")
    if not tournament_id:
        flash("Турнир не выбран", "error")
        return redirect("/dashboard")

    Tournaments.update(status="finished").where(Tournaments.id == int(tournament_id)).execute()
    flash("Турнир завершен", "success")
    return redirect("/dashboard")


@application.route("/confirm_match_result", methods=["POST"])
@login_required
def confirm_match_result():
    """Админ подтверждает отправленный капитаном результат; матч становится confirmed."""
    if current_user.role_id.id != 1:
        return redirect("/logout")

    match_id = request.form.get("match_id")
    if not match_id:
        flash("Матч не выбран", "error")
        return redirect("/dashboard")

    result = (
        Match_results.select()
        .where((Match_results.match_id == int(match_id)) & (Match_results.confirmed_by.is_null(True)))
        .order_by(Match_results.id.desc())
        .first()
    )

    if result is None:
        flash("Неподтверждённый результат не найден", "error")
        return redirect("/dashboard")

    Match_results.update(confirmed_by=current_user.id).where(Match_results.id == result.id).execute()
    Matches.update(status="confirmed").where(Matches.id == int(match_id)).execute()

    # Генерируем следующий раунд
    match = Matches.get_by_id(int(match_id))
    generate_next_round(match.tournament_id.id)

    flash("Счёт подтверждён", "success")
    return redirect("/dashboard")


@application.route("/admin/reject_match_result", methods=["POST"])
@login_required
def admin_reject_match_result():
    """Админ отклоняет (аннулирует) результат матча, возвращая его в статус pending."""
    if current_user.role_id.id != 1:
        flash("Доступ запрещен", "error")
        return redirect("/dashboard")

    match_id = request.form.get("match_id")
    if not match_id:
        flash("Матч не выбран", "error")
        return redirect("/dashboard")

    result = (
        Match_results.select()
        .where(Match_results.match_id == int(match_id))
        .order_by(Match_results.id.desc())
        .first()
    )

    if result is None:
        flash("Результат не найден", "error")
        return redirect("/dashboard")

    if result.confirmed_by_id is not None:
        Match_results.update(confirmed_by=None).where(Match_results.id == result.id).execute()

    Match_map_score.delete().where(Match_map_score.match_id == int(match_id)).execute()
    Match_results.delete().where(Match_results.id == result.id).execute()

    Matches.update(
        status="pending",
        winner_id=None
    ).where(Matches.id == int(match_id)).execute()

    flash("Результат матча аннулирован. Капитаны могут отправить новый результат.", "success")
    return redirect("/dashboard")


@application.route("/captain/appeal_match", methods=["POST"])
@login_required
def captain_appeal_match():
    """Капитан подает апелляцию на результат матча (если не согласен)."""
    if current_user.role_id.id != 2:
        flash("Доступ запрещен", "error")
        return redirect("/dashboard")

    team = captain_team()
    if not team:
        flash("Вы не являетесь капитаном команды", "error")
        return redirect("/dashboard")

    match_id = request.form.get("match_id")
    if not match_id:
        flash("Матч не выбран", "error")
        return redirect("/dashboard")

    match = Matches.get_or_none(Matches.id == int(match_id))
    if not match:
        flash("Матч не найден", "error")
        return redirect("/dashboard")

    if match.team1_id.id != team.id and match.team2_id.id != team.id:
        flash("Это не ваш матч", "error")
        return redirect("/dashboard")

    if match.status != "confirmed":
        flash("Матч еще не подтвержден администратором", "error")
        return redirect("/dashboard")

    result = Match_results.get_or_none(Match_results.match_id == match.id)
    if not result:
        flash("Результат не найден", "error")
        return redirect("/dashboard")

    if result.appealed_by_id is not None:
        flash("Апелляция уже подана", "error")
        return redirect("/dashboard")

    Match_results.update(
        appealed_by=current_user.id,
        appeal_reason=request.form.get("appeal_reason", "Капитан не согласен с результатом")
    ).where(Match_results.id == result.id).execute()

    Matches.update(status="appeal").where(Matches.id == match.id).execute()

    flash("Апелляция подана. Администратор рассмотрит ее.", "info")
    return redirect("/dashboard")


@application.route("/admin/appeal_resolve", methods=["POST"])
@login_required
def admin_resolve_appeal():
    """Админ разрешает апелляцию."""
    if current_user.role_id.id != 1:
        flash("Доступ запрещен", "error")
        return redirect("/dashboard")

    match_id = request.form.get("match_id")
    action = request.form.get("action")  # "confirm" или "reject"

    if not match_id or not action:
        flash("Неверные данные", "error")
        return redirect("/dashboard")

    match = Matches.get_or_none(Matches.id == int(match_id))
    if not match:
        flash("Матч не найден", "error")
        return redirect("/dashboard")

    result = Match_results.get_or_none(Match_results.match_id == match.id)
    if not result:
        flash("Результат не найден", "error")
        return redirect("/dashboard")

    if action == "reject":
        # ===== ОТКЛОНИТЬ АПЕЛЛЯЦИЮ =====
        # Апелляция ложная - результат подтверждается
        Match_results.update(
            confirmed_by=current_user.id,
            appealed_by=None,
            appeal_reason=None
        ).where(Match_results.id == result.id).execute()
        Matches.update(status="confirmed").where(Matches.id == match.id).execute()

        # Генерируем следующий раунд
        generate_next_round(match.tournament_id.id)

        flash("Апелляция отклонена. Результат подтвержден.", "success")

    elif action == "confirm":
        # ===== ПОДТВЕРДИТЬ АПЕЛЛЯЦИЮ =====
        # Апелляция верная - капитан соврал
        # Получаем пользователя, который подал апелляцию
        appealing_user = result.appealed_by

        # Пытаемся найти команду пользователя через Team_members
        team_member = Team_members.get_or_none(Team_members.user_id == appealing_user.id)

        if not team_member:
            # Если пользователь не найден в team_members,
            # определяем его команду по match (он должен быть капитаном одной из команд)
            if match.team1_id and match.team1_id.captain_id.id == appealing_user.id:
                appealing_team = match.team1_id
            elif match.team2_id and match.team2_id.captain_id.id == appealing_user.id:
                appealing_team = match.team2_id
            else:
                flash("Ошибка: пользователь не является капитаном команды", "error")
                return redirect("/dashboard")
        else:
            appealing_team = team_member.team_id

        # Определяем, какая команда подала апелляцию (team1 или team2)
        if match.team1_id.id == appealing_team.id:
            appealing_team_id = match.team1_id.id
            lying_team = match.team2_id
            # Создаем новый результат с победой команды, подавшей апелляцию
            Match_results.create(
                match_id=match.id,
                score_team1=2,
                score_team2=0,
                reported_by=current_user.id,
                confirmed_by=current_user.id,
                appealed_by=None,
                appeal_reason=None,
                win_reason=f"Победа команды {appealing_team.name} по причине введения в заблуждение (капитан команды {lying_team.name} предоставил ложный результат)"
            )
        else:
            appealing_team_id = match.team2_id.id
            lying_team = match.team1_id
            Match_results.create(
                match_id=match.id,
                score_team1=0,
                score_team2=2,
                reported_by=current_user.id,
                confirmed_by=current_user.id,
                appealed_by=None,
                appeal_reason=None,
                win_reason=f"Победа команды {appealing_team.name} по причине введения в заблуждение (капитан команды {lying_team.name} предоставил ложный результат)"
            )

        # Удаляем старый результат и карты
        Match_map_score.delete().where(Match_map_score.match_id == match.id).execute()
        Match_results.delete().where(Match_results.id == result.id).execute()

        # Обновляем матч - победитель и статус confirmed
        Matches.update(
            winner_id=appealing_team_id,
            status="confirmed"
        ).where(Matches.id == match.id).execute()

        # Генерируем следующий раунд
        generate_next_round(match.tournament_id.id)

        flash(f"Апелляция подтверждена. Команда {lying_team.name} дисквалифицирована за предоставление ложного результата.", "warning")

    return redirect("/dashboard")


@application.route("/logout", methods=["GET"])
@login_required
def logout():
    """Выход из аккаунта (очистка сессии Flask-Login)."""
    logout_user()
    return redirect("/")


app = application

if __name__ == "__main__":
    init_db()
    application.run(host='0.0.0.0', debug=True, port=5000)