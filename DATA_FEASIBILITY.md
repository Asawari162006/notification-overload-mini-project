# Dataset feasibility

{
  "source": "https://github.com/komis1/ami2018-notifications",
  "retrieval_date": "2026-10-08",
  "sha256": "214c40433a118eba1d6caf986b3fa5bcb690eb725203997a8c7f31b3840e5594",
  "citation": "Komninos, A., Frengkou, E., & Garofalakis, J. (2018). Predicting User Responsiveness to Smartphone Notifications for Edge Computing. AmI-18, Springer, Larnaca, Cyprus.",
  "usage_terms": "Repository GPL-3.0; README permits use for any purpose and requests academic citation. Preserve upstream license; no public redistribution performed.",
  "raw_rows": 176195,
  "participants": 14,
  "distinct_participant_traces": 13,
  "duplicate_participant_traces": {
    "7": "6"
  },
  "timestamp_units": "Unix seconds (10-digit values, 2018 range); SQL session +00:00. Participant local timezones unknown; calendar features omitted.",
  "schema": "-- phpMyAdmin SQL Dump\n-- version 4.0.2\n-- http://www.phpmyadmin.net\n--\n-- Host: localhost\n-- Generation Time: Aug 14, 2018 at 12:29 PM\n-- Server version: 5.6.33-0ubuntu0.14.04.1\n-- PHP Version: 5.5.9-1ubuntu4.25\n\nSET SQL_MODE = \"NO_AUTO_VALUE_ON_ZERO\";\nSET time_zone = \"+00:00\";\n\n\n/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;\n/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;\n/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;\n/*!40101 SET NAMES utf8 */;\n\n--\n-- Database: `test`\n--\n\n-- --------------------------------------------------------\n\n--\n-- Table structure for table `elton_notifications`\n--\n\nCREATE TABLE IF NOT EXISTS `elton_notifications` (\n  `user_id` varchar(40) NOT NULL,\n  `id` int(11) NOT NULL,\n  `nid` int(11) NOT NULL,\n  `priority` int(11) NOT NULL,\n  `packageName` text NOT NULL,\n  `timePosted` int(11) NOT NULL,\n  `timeRemoved` int(11) NOT NULL,\n  `sound` int(11) NOT NULL,\n  `default_Sound` int(11) NOT NULL,\n  `LED` int(11) NOT NULL,\n  `default_LED` int(11) NOT NULL,\n  `VibrationPattern` text NOT NULL,\n  `default_Vibration` int(11) NOT NULL,\n  `ringerMode` int(11) NOT NULL,\n  `PlaceName` text NOT NULL,\n  `PlaceId` text NOT NULL,\n  `place_confidence` double NOT NULL,\n  `placeCategories` text NOT NULL,\n  `lat` double NOT NULL,\n  `lng` double NOT NULL,\n  `idle` int(11) NOT NULL,\n  `interactive` int(11) NOT NULL,\n  `screen_state` int(11) NOT NULL,\n  `lock_scr_notifs` int(11) NOT NULL,\n  `flags` int(11) NOT NULL,\n  UNIQUE KEY `user_id` (`user_id`,`id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8;\n\n--\n-- Dumping data for table `elton_notifications`\n--\n\n",
  "types": {
    "participant": "object",
    "id": "int64",
    "nid": "int64",
    "priority": "int64",
    "source": "object",
    "posted_at": "int64",
    "removed_at": "int64",
    "sound": "int64",
    "default_sound": "int64",
    "led": "int64",
    "default_led": "int64",
    "vibrationpattern": "object",
    "default_vibration": "int64",
    "ringer": "int64",
    "idle": "int64",
    "interactive": "int64",
    "screen_state": "int64",
    "lock_scr_notifs": "int64",
    "flags": "int64"
  },
  "missingness": {
    "participant": 0,
    "id": 0,
    "nid": 0,
    "priority": 0,
    "source": 0,
    "posted_at": 0,
    "removed_at": 0,
    "sound": 0,
    "default_sound": 0,
    "led": 0,
    "default_led": 0,
    "vibrationpattern": 0,
    "default_vibration": 0,
    "ringer": 0,
    "idle": 0,
    "interactive": 0,
    "screen_state": 0,
    "lock_scr_notifs": 0,
    "flags": 0
  },
  "zero_removal_records": 120380,
  "invalid_order_records": 4,
  "duplicate_serial_ids": 0,
  "duplicate_posting_identity": 33811,
  "exclusions": {
    "unknown_removal": 94147,
    "usable": 43848,
    "duplicate_participant_trace": 2929,
    "overlapping_identity": 1456,
    "negative_duration": 4
  },
  "usable_samples": 43848,
  "zero_durations": 7774,
  "duration_quantiles": {
    "0.0": 0.0,
    "0.25": 1.0,
    "0.5": 5.0,
    "0.75": 56.0,
    "0.95": 1800.0,
    "0.99": 8421.78999999995,
    "1.0": 134147.0
  },
  "endpoints": [
    {
      "participant": "1",
      "first_post": 1526473551,
      "last_post": 1528232398,
      "last_recorded_removal": 1528231694
    },
    {
      "participant": "10",
      "first_post": 1526162990,
      "last_post": 1528226264,
      "last_recorded_removal": 1528226264
    },
    {
      "participant": "11",
      "first_post": 1526061511,
      "last_post": 1528231774,
      "last_recorded_removal": 1528231799
    },
    {
      "participant": "12",
      "first_post": 1526078873,
      "last_post": 1527872166,
      "last_recorded_removal": 1527872118
    },
    {
      "participant": "13",
      "first_post": 1527067713,
      "last_post": 1528231229,
      "last_recorded_removal": 1528231229
    },
    {
      "participant": "14",
      "first_post": 1526574948,
      "last_post": 1528228171,
      "last_recorded_removal": 1528229456
    },
    {
      "participant": "2",
      "first_post": 1525665596,
      "last_post": 1528231162,
      "last_recorded_removal": 1528232662
    },
    {
      "participant": "3",
      "first_post": 1526310940,
      "last_post": 1528232286,
      "last_recorded_removal": 1528232385
    },
    {
      "participant": "4",
      "first_post": 1526492552,
      "last_post": 1528231504,
      "last_recorded_removal": 1528232708
    },
    {
      "participant": "5",
      "first_post": 1526053720,
      "last_post": 1528231184,
      "last_recorded_removal": 1528231418
    },
    {
      "participant": "6",
      "first_post": 1526306972,
      "last_post": 1528228874,
      "last_recorded_removal": 1528228877
    },
    {
      "participant": "7",
      "first_post": 1526306972,
      "last_post": 1528228874,
      "last_recorded_removal": 1528228877
    },
    {
      "participant": "8",
      "first_post": 1526285689,
      "last_post": 1528232398,
      "last_recorded_removal": 1528232003
    },
    {
      "participant": "9",
      "first_post": 1526302767,
      "last_post": 1528231168,
      "last_recorded_removal": 1528231289
    }
  ],
  "removal_reasons": "Not available",
  "followup": "Observation endpoints are last logged events, not verified monitoring end times. Missing removal is unknown, not established censoring."
}

## Decision before training
Observed-duration regression is supportable only for conservative, unambiguous recorded posting episodes. Same participant/package/nid/posting-second rows are consolidated, taking earliest serial metadata. Conflicting removals and identities with another posting strictly before removal are excluded. Android notification tags and first lifecycle posting are absent: identities cannot be fully reconstructed. Zero-removal rows at earlier posting times cannot safely be attached to later removals. This target is recorded posting-to-removal, not a proven complete notification lifetime. All exclusions have raw serial lineage. Participant 7 is an exact copy of participant 6 after removing participant ID; trace 7 is preserved but excluded from supervised evaluation and history to prevent leakage. The 14 IDs represent only 13 distinct recorded traces; identity of people cannot be verified. Valid extremes and zero durations are retained.

The included sample is selected on observed removal and unambiguous identity, and may overrepresent short durations. Evaluation does not apply to all phone notifications. No defensible censoring endpoints or removal reasons exist; survival analysis and optional horizon classification are deferred. Timestamp magnitudes demonstrate seconds despite Android API millisecond output. No local-calendar assumptions are made.
