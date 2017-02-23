SET FOREIGN_KEY_CHECKS=0;

DROP TABLE IF EXISTS `category`;
CREATE TABLE `category` (
  `id` int(3) NOT NULL,
  `num` int(3) NOT NULL,
  `title` varchar(500) DEFAULT NULL,
  `name` varchar(500) DEFAULT NULL,
  `url` varchar(100) DEFAULT NULL,
  `state` int(1) DEFAULT NULL,
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `url` (`url`),
  KEY `num` (`num`),
  KEY `id_2` (`id`,`num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET FOREIGN_KEY_CHECKS=1;
