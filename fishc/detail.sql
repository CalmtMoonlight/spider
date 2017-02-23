SET FOREIGN_KEY_CHECKS=0;

DROP TABLE IF EXISTS `detail`;
CREATE TABLE `detail` (
  `id` int(3) NOT NULL,
  `num` int(3) DEFAULT NULL,
  `name` varchar(500) DEFAULT NULL,
  `link` varchar(100) NOT NULL,
  `_link` varchar(100) DEFAULT NULL,
  `_verify` char(4) DEFAULT NULL,
  `state` int(1) DEFAULT NULL,
  PRIMARY KEY (`link`),
  KEY `id` (`id`,`num`),
  CONSTRAINT `detail_ibfk_1` FOREIGN KEY (`id`, `num`) REFERENCES `category` (`id`, `num`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET FOREIGN_KEY_CHECKS=1;
