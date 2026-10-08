# Data dictionary

-- phpMyAdmin SQL Dump
-- version 4.0.2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Aug 14, 2018 at 12:29 PM
-- Server version: 5.6.33-0ubuntu0.14.04.1
-- PHP Version: 5.5.9-1ubuntu4.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `test`
--

-- --------------------------------------------------------

--
-- Table structure for table `elton_notifications`
--

CREATE TABLE IF NOT EXISTS `elton_notifications` (
  `user_id` varchar(40) NOT NULL,
  `id` int(11) NOT NULL,
  `nid` int(11) NOT NULL,
  `priority` int(11) NOT NULL,
  `packageName` text NOT NULL,
  `timePosted` int(11) NOT NULL,
  `timeRemoved` int(11) NOT NULL,
  `sound` int(11) NOT NULL,
  `default_Sound` int(11) NOT NULL,
  `LED` int(11) NOT NULL,
  `default_LED` int(11) NOT NULL,
  `VibrationPattern` text NOT NULL,
  `default_Vibration` int(11) NOT NULL,
  `ringerMode` int(11) NOT NULL,
  `PlaceName` text NOT NULL,
  `PlaceId` text NOT NULL,
  `place_confidence` double NOT NULL,
  `placeCategories` text NOT NULL,
  `lat` double NOT NULL,
  `lng` double NOT NULL,
  `idle` int(11) NOT NULL,
  `interactive` int(11) NOT NULL,
  `screen_state` int(11) NOT NULL,
  `lock_scr_notifs` int(11) NOT NULL,
  `flags` int(11) NOT NULL,
  UNIQUE KEY `user_id` (`user_id`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `elton_notifications`
--



INSERT records populate 19 fields; six declared location fields are omitted and not predictors. user_id is participant; id is device logging serial unique with user_id; nid is reusable Android notification ID, not globally unique. packageName is source. timePosted/timeRemoved are stored Unix seconds, zero removal means unknown. priority is programmed priority, not importance. ringerMode, idle, interactive and screen_state are device context. Sound/LED/vibration/defaults/flags are recorded programming metadata. No removal reason, Android tag, monitoring endpoint or participant timezone is supplied. Derived fields: episode_id, raw_ids, reason, duration_seconds. See lineage.csv for every record group.
