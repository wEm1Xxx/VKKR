-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Хост: 127.0.0.1
-- Время создания: Июн 22 2026 г., 20:45
-- Версия сервера: 10.4.32-MariaDB
-- Версия PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `tournament`
--

-- --------------------------------------------------------

--
-- Структура таблицы `cs2_pickban`
--

CREATE TABLE `cs2_pickban` (
  `id` int(11) NOT NULL,
  `match_id` int(11) NOT NULL,
  `step` int(11) NOT NULL,
  `action` varchar(20) NOT NULL,
  `map_name` varchar(64) NOT NULL,
  `team_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `cs2_pickban`
--

INSERT INTO `cs2_pickban` (`id`, `match_id`, `step`, `action`, `map_name`, `team_id`) VALUES
(1, 2, 1, 'ban', 'Ancient', 1),
(2, 2, 2, 'ban', 'Anubis', 3),
(3, 2, 3, 'pick', 'Inferno', 1),
(4, 2, 4, 'pick', 'Mirage', 3),
(5, 2, 5, 'ban', 'Dust 2', 1),
(6, 2, 6, 'ban', 'Overpass', 3),
(7, 2, 7, 'decider', 'Nuke', NULL);

-- --------------------------------------------------------

--
-- Структура таблицы `matches`
--

CREATE TABLE `matches` (
  `id` int(11) NOT NULL,
  `tournament_id` int(11) NOT NULL,
  `round` int(11) NOT NULL,
  `team1_id` int(11) DEFAULT NULL,
  `team2_id` int(11) DEFAULT NULL,
  `scheduled_time` datetime DEFAULT NULL,
  `winner_id` int(11) DEFAULT NULL,
  `status` enum('pending','veto','finished','confirmed','appeal','final') DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `matches`
--

INSERT INTO `matches` (`id`, `tournament_id`, `round`, `team1_id`, `team2_id`, `scheduled_time`, `winner_id`, `status`) VALUES
(1, 2, 1, 1, 3, NULL, 3, 'confirmed'),
(2, 3, 1, 1, 3, NULL, 3, 'confirmed');

-- --------------------------------------------------------

--
-- Структура таблицы `match_map_score`
--

CREATE TABLE `match_map_score` (
  `id` int(11) NOT NULL,
  `match_id` int(11) NOT NULL,
  `map_name` varchar(64) NOT NULL,
  `team1_rounds` int(11) NOT NULL,
  `team2_rounds` int(11) NOT NULL,
  `map_order` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `match_map_score`
--

INSERT INTO `match_map_score` (`id`, `match_id`, `map_name`, `team1_rounds`, `team2_rounds`, `map_order`) VALUES
(1, 2, 'Inferno', 13, 9, 1),
(2, 2, 'Mirage', 4, 13, 2),
(3, 2, 'Nuke', 20, 22, 3);

-- --------------------------------------------------------

--
-- Структура таблицы `match_results`
--

CREATE TABLE `match_results` (
  `id` int(11) NOT NULL,
  `match_id` int(11) NOT NULL,
  `score_team1` int(11) NOT NULL,
  `score_team2` int(11) NOT NULL,
  `reported_by` int(11) NOT NULL,
  `confirmed_by` int(11) DEFAULT NULL,
  `confirmed_at` datetime DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `appealed_by` int(11) DEFAULT NULL,
  `appeal_reason` text DEFAULT NULL,
  `win_reason` text DEFAULT NULL,
  `agreed_by_team1` tinyint(1) DEFAULT 0,
  `agreed_by_team2` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `match_results`
--

INSERT INTO `match_results` (`id`, `match_id`, `score_team1`, `score_team2`, `reported_by`, `confirmed_by`, `confirmed_at`, `created_at`, `appealed_by`, `appeal_reason`, `win_reason`, `agreed_by_team1`, `agreed_by_team2`) VALUES
(1, 1, 1, 2, 14, 13, NULL, '2026-05-06 23:32:16', NULL, NULL, NULL, 0, 0),
(2, 2, 1, 2, 15, 13, NULL, '2026-05-07 00:15:06', NULL, NULL, NULL, 0, 0);

-- --------------------------------------------------------

--
-- Структура таблицы `roles`
--

CREATE TABLE `roles` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `roles`
--

INSERT INTO `roles` (`id`, `name`) VALUES
(1, 'Администратор'),
(4, 'Зритель'),
(3, 'Игрок'),
(2, 'Капитан');

-- --------------------------------------------------------

--
-- Структура таблицы `teams`
--

CREATE TABLE `teams` (
  `id` int(11) NOT NULL,
  `name` varchar(120) NOT NULL,
  `captain_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `teams`
--

INSERT INTO `teams` (`id`, `name`, `captain_id`, `created_at`) VALUES
(1, 'Team Alpha', 14, '2026-05-06 12:06:22'),
(2, 'Team Beta', 3, '2026-05-06 12:06:22'),
(3, 'Qwerty', 15, '2026-05-06 22:40:04'),
(4, 'Drakoni', 21, '2026-06-22 12:52:35');

-- --------------------------------------------------------

--
-- Структура таблицы `team_join_requests`
--

CREATE TABLE `team_join_requests` (
  `id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `player_id` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `team_join_requests`
--

INSERT INTO `team_join_requests` (`id`, `team_id`, `player_id`, `status`, `created_at`) VALUES
(1, 1, 12, 'approved', '2026-05-07 03:33:33'),
(2, 2, 12, 'pending', '2026-05-07 03:33:35'),
(3, 3, 12, 'rejected', '2026-05-07 04:14:34'),
(4, 3, 16, 'approved', '2026-05-07 04:24:36'),
(5, 1, 20, 'pending', '2026-06-22 17:24:36');

-- --------------------------------------------------------

--
-- Структура таблицы `team_members`
--

CREATE TABLE `team_members` (
  `id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `joined_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `team_members`
--

INSERT INTO `team_members` (`id`, `team_id`, `user_id`, `joined_at`) VALUES
(3, 2, 3, '2026-05-06 12:06:49'),
(4, 2, 5, '2026-05-06 12:10:02'),
(5, 1, 12, '2026-05-06 22:37:48'),
(6, 3, 15, '2026-05-06 22:40:04'),
(7, 3, 16, '2026-05-06 23:24:47'),
(8, 4, 21, '2026-06-22 12:52:35');

-- --------------------------------------------------------

--
-- Структура таблицы `tournaments`
--

CREATE TABLE `tournaments` (
  `id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `game` varchar(255) NOT NULL,
  `format` enum('single_elimination','round_robin') NOT NULL,
  `max_teams` int(11) NOT NULL,
  `start_date` datetime NOT NULL,
  `status` enum('draft','registration','in_progress','finished') DEFAULT 'draft',
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `tournaments`
--

INSERT INTO `tournaments` (`id`, `title`, `game`, `format`, `max_teams`, `start_date`, `status`, `created_by`, `created_at`) VALUES
(2, 'YMK Spring1', 'Dota 2', 'single_elimination', 8, '2026-05-12 16:25:00', 'finished', 13, '2026-05-06 22:19:13'),
(3, 'YMK Spring1', 'CS2', 'single_elimination', 2, '2026-05-28 21:40:00', 'finished', 13, '2026-05-06 23:37:14');

-- --------------------------------------------------------

--
-- Структура таблицы `tournament_registrations`
--

CREATE TABLE `tournament_registrations` (
  `id` int(11) NOT NULL,
  `tournament_id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `registered_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `tournament_registrations`
--

INSERT INTO `tournament_registrations` (`id`, `tournament_id`, `team_id`, `registered_at`) VALUES
(5, 2, 1, '2026-05-06 22:37:53'),
(6, 2, 3, '2026-05-06 23:25:02'),
(7, 3, 1, '2026-05-06 23:37:36'),
(8, 3, 3, '2026-05-06 23:37:49');

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `role_id`, `created_at`) VALUES
(1, 'admin', 'admin@example.com', '$2b$12$admin_hash_example', 1, '2026-05-06 12:05:07'),
(2, 'cap_one', 'cap1@example.com', '$2b$12$cap1_hash_example', 2, '2026-05-06 12:05:07'),
(3, 'cap_two', 'cap2@example.com', '$2b$12$cap2_hash_example', 2, '2026-05-06 12:05:07'),
(4, 'player_one', 'player1@example.com', '$2b$12$player1_hash_example', 3, '2026-05-06 12:05:07'),
(5, 'player_two', 'player2@example.com', '$2b$12$player2_hash_example', 3, '2026-05-06 12:09:29'),
(12, 'wEm1Xxx', 'sergeygevkan352006@gmail.com', '$2b$12$SQeafxZ8R7kTt.B395nLe.aiiDlzD/XxdY3S91olQJeV8fG7DejzG', 3, '2026-05-06 21:43:55'),
(13, 'admin1', 'admin@admin.admin', '$2b$12$Ul.cuPMcZddZDoOisNx7.OW2dv8qkI3BcrDGODqw6l/0KQm48RA4a', 1, '2026-05-06 21:48:40'),
(14, 'cap1', 'cap@cap.cap', '$2b$12$nDHpGgkAUYePfs1t2Bf8wuk.NwXn79iRFfjP6AkajbDZJqFIl1i02', 2, '2026-05-06 22:20:07'),
(15, 'cap2', 'cap2@cap.cap', '$2b$12$mHNI/ci6SCWHCDyz1AY4PuY/YmqGcr0Tg0ue2kqzSmkJkyzskWule', 2, '2026-05-06 22:39:45'),
(16, 'player', 'player@player.player', '$2b$12$IS4lA3lUWFclM5n7ywErL.txjOlqC3lkLtH.ZAKCEUqokX1RW2d/i', 3, '2026-05-06 23:24:12'),
(20, 'Grisha', 'grisha@gmail.com', '$2b$12$4XdiO6FAxuufcT34m.JPiOsEF4fTxrLYeFTmz0bgEGwh41DL5xMom', 3, '2026-06-22 12:24:14'),
(21, 'Sila4', 'sila4@gmail.com', '$2b$12$zFVBTdxZE7ZEzSejyjLYFODXPin96QYFBg77IoteorkryHv3ZTk7m', 2, '2026-06-22 12:52:15');

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `cs2_pickban`
--
ALTER TABLE `cs2_pickban`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cs2_pickban_match_id` (`match_id`),
  ADD KEY `cs2_pickban_team_id` (`team_id`);

--
-- Индексы таблицы `matches`
--
ALTER TABLE `matches`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_matches_tournament` (`tournament_id`),
  ADD KEY `fk_matches_team1` (`team1_id`),
  ADD KEY `fk_matches_team2` (`team2_id`),
  ADD KEY `fk_matches_winner` (`winner_id`);

--
-- Индексы таблицы `match_map_score`
--
ALTER TABLE `match_map_score`
  ADD PRIMARY KEY (`id`),
  ADD KEY `match_map_score_match_id` (`match_id`);

--
-- Индексы таблицы `match_results`
--
ALTER TABLE `match_results`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_match_results_match` (`match_id`),
  ADD KEY `fk_match_results_reported_by` (`reported_by`),
  ADD KEY `fk_match_results_confirmed_by` (`confirmed_by`),
  ADD KEY `fk_match_results_appealed_by` (`appealed_by`);

--
-- Индексы таблицы `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Индексы таблицы `teams`
--
ALTER TABLE `teams`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `fk_teams_captain` (`captain_id`);

--
-- Индексы таблицы `team_join_requests`
--
ALTER TABLE `team_join_requests`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `team_join_requests_team_id_player_id` (`team_id`,`player_id`),
  ADD KEY `team_join_requests_team_id` (`team_id`),
  ADD KEY `team_join_requests_player_id` (`player_id`);

--
-- Индексы таблицы `team_members`
--
ALTER TABLE `team_members`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_team_user` (`team_id`,`user_id`),
  ADD KEY `fk_team_members_user` (`user_id`);

--
-- Индексы таблицы `tournaments`
--
ALTER TABLE `tournaments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_tournaments_creator` (`created_by`);

--
-- Индексы таблицы `tournament_registrations`
--
ALTER TABLE `tournament_registrations`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_tournament_team` (`tournament_id`,`team_id`),
  ADD KEY `fk_registrations_team` (`team_id`);

--
-- Индексы таблицы `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `fk_users_role` (`role_id`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `cs2_pickban`
--
ALTER TABLE `cs2_pickban`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=64;

--
-- AUTO_INCREMENT для таблицы `matches`
--
ALTER TABLE `matches`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT для таблицы `match_map_score`
--
ALTER TABLE `match_map_score`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT для таблицы `match_results`
--
ALTER TABLE `match_results`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT для таблицы `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT для таблицы `teams`
--
ALTER TABLE `teams`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT для таблицы `team_join_requests`
--
ALTER TABLE `team_join_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT для таблицы `team_members`
--
ALTER TABLE `team_members`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT для таблицы `tournaments`
--
ALTER TABLE `tournaments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT для таблицы `tournament_registrations`
--
ALTER TABLE `tournament_registrations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- Ограничения внешнего ключа сохраненных таблиц
--

--
-- Ограничения внешнего ключа таблицы `cs2_pickban`
--
ALTER TABLE `cs2_pickban`
  ADD CONSTRAINT `cs2_pickban_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `cs2_pickban_ibfk_2` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE SET NULL;

--
-- Ограничения внешнего ключа таблицы `matches`
--
ALTER TABLE `matches`
  ADD CONSTRAINT `fk_matches_team1` FOREIGN KEY (`team1_id`) REFERENCES `teams` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_matches_team2` FOREIGN KEY (`team2_id`) REFERENCES `teams` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_matches_tournament` FOREIGN KEY (`tournament_id`) REFERENCES `tournaments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_matches_winner` FOREIGN KEY (`winner_id`) REFERENCES `teams` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Ограничения внешнего ключа таблицы `match_map_score`
--
ALTER TABLE `match_map_score`
  ADD CONSTRAINT `match_map_score_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `match_results`
--
ALTER TABLE `match_results`
  ADD CONSTRAINT `fk_match_results_appealed_by` FOREIGN KEY (`appealed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_match_results_confirmed_by` FOREIGN KEY (`confirmed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_match_results_match` FOREIGN KEY (`match_id`) REFERENCES `matches` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_match_results_reported_by` FOREIGN KEY (`reported_by`) REFERENCES `users` (`id`) ON UPDATE CASCADE;

--
-- Ограничения внешнего ключа таблицы `teams`
--
ALTER TABLE `teams`
  ADD CONSTRAINT `fk_teams_captain` FOREIGN KEY (`captain_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE;

--
-- Ограничения внешнего ключа таблицы `team_join_requests`
--
ALTER TABLE `team_join_requests`
  ADD CONSTRAINT `team_join_requests_ibfk_1` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `team_join_requests_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `team_members`
--
ALTER TABLE `team_members`
  ADD CONSTRAINT `fk_team_members_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_team_members_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Ограничения внешнего ключа таблицы `tournaments`
--
ALTER TABLE `tournaments`
  ADD CONSTRAINT `fk_tournaments_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON UPDATE CASCADE;

--
-- Ограничения внешнего ключа таблицы `tournament_registrations`
--
ALTER TABLE `tournament_registrations`
  ADD CONSTRAINT `fk_registrations_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_registrations_tournament` FOREIGN KEY (`tournament_id`) REFERENCES `tournaments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Ограничения внешнего ключа таблицы `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
