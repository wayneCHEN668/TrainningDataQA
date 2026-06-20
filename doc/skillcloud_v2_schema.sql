/*
SQLyog Ultimate v12.09 (64 bit)
MySQL - 8.0.45-0ubuntu0.24.04.1 : Database - skillcloud_v2
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`skillcloud_v2` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `skillcloud_v2`;

/*Table structure for table `admin_dept` */

DROP TABLE IF EXISTS `admin_dept`;

CREATE TABLE `admin_dept` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '管理员 user_id',
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属一级单位编号（一级单位）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_admin_user` (`user_id`),
  UNIQUE KEY `uk_admin_dept` (`dept_code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员-一级单位归属表（1:1）';

/*Table structure for table `ai_learning_plan` */

DROP TABLE IF EXISTS `ai_learning_plan`;

CREATE TABLE `ai_learning_plan` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学习者 user_id',
  `path_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联路径（NULL=初次规划尚未生成路径）',
  `trigger_type` tinyint NOT NULL DEFAULT '0' COMMENT '0=初始 1=里程碑 2=用户请求 3=管理员 4=定期重评',
  `trigger_detail` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '触发说明（如"完成节点3"）',
  `llm_input_context` json DEFAULT NULL COMMENT 'LLM 输入 context（学习摘要/进度/技能缺口/偏好）',
  `llm_prompt_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '使用的 Prompt 版本号',
  `llm_suggestion_text` text COLLATE utf8mb4_unicode_ci COMMENT 'LLM 自然语言建议（展示给学习者）',
  `suggested_path` json DEFAULT NULL COMMENT 'LLM 建议的课程序列（结构化）',
  `skill_gap_analysis` text COLLATE utf8mb4_unicode_ci COMMENT 'LLM 技能缺口分析',
  `feedback_status` tinyint NOT NULL DEFAULT '0' COMMENT '0=未反馈 1=接受 2=拒绝 3=部分接受',
  `feedback_note` text COLLATE utf8mb4_unicode_ci COMMENT '用户反馈备注',
  `applied_at` datetime DEFAULT NULL COMMENT '建议被应用的时间',
  `planned_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_alp_user` (`user_id`),
  KEY `idx_alp_path` (`path_code`),
  KEY `idx_alp_trigger` (`trigger_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 学习规划记录（LLM 输入/输出/反馈完整存档）';

/*Table structure for table `alembic_version` */

DROP TABLE IF EXISTS `alembic_version`;

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `announcement` */

DROP TABLE IF EXISTS `announcement`;

CREATE TABLE `announcement` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `notice_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告唯一编号',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `content` longtext COLLATE utf8mb4_unicode_ci COMMENT '内容（HTML）',
  `published_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL COMMENT '过期时间（NULL=永久）',
  `notice_type` int NOT NULL DEFAULT '0' COMMENT '0=系统公告 1=课程通知',
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `publisher_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_notice_code` (`notice_code`),
  KEY `idx_ann_org` (`org_code`),
  KEY `idx_ann_published` (`published_at`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公告内容表';

/*Table structure for table `announcement_target` */

DROP TABLE IF EXISTS `announcement_target`;

CREATE TABLE `announcement_target` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `notice_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联 announcement.notice_code',
  `target_type` tinyint NOT NULL COMMENT '投放维度: 0=全机构 1=班级 2=课程 3=岗位',
  `target_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对应 class_code 或 course_code',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_at_notice` (`notice_code`),
  KEY `idx_at_target` (`target_type`,`target_code`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `announcement_template` */

DROP TABLE IF EXISTS `announcement_template`;

CREATE TABLE `announcement_template` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `template_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模板唯一编号',
  `template_body` text COLLATE utf8mb4_unicode_ci COMMENT '模板内容（支持 {{变量}} 占位符）',
  `is_auto` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否自动触发',
  `template_desc` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_template_code` (`template_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公告消息模板表';

/*Table structure for table `app_version` */

DROP TABLE IF EXISTS `app_version`;

CREATE TABLE `app_version` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `platform` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'android / ios',
  `version` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '版本号',
  `download_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `release_note` text COLLATE utf8mb4_unicode_ci,
  `is_force_update` tinyint(1) NOT NULL DEFAULT '0',
  `released_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_av_platform` (`platform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='移动端应用版本表';

/*Table structure for table `assignment` */

DROP TABLE IF EXISTS `assignment`;

CREATE TABLE `assignment` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `assignment_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '作业唯一编号',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '作业标题',
  `description` text COLLATE utf8mb4_unicode_ci,
  `full_score` int NOT NULL DEFAULT '100',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联课程',
  `creator_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '创建教师 user_id',
  `published_at` datetime DEFAULT NULL,
  `submit_start` date DEFAULT NULL COMMENT '开放提交开始日期',
  `submit_end` date DEFAULT NULL COMMENT '截止提交日期',
  `is_closed` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否关闭',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_assignment_code` (`assignment_code`),
  KEY `idx_asgn_course` (`course_code`),
  KEY `idx_asgn_creator` (`creator_id`),
  KEY `idx_asgn_end` (`submit_end`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业信息表';

/*Table structure for table `assignment_answer` */

DROP TABLE IF EXISTS `assignment_answer`;

CREATE TABLE `assignment_answer` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `question_id` int unsigned NOT NULL COMMENT '关联 assignment_question.id',
  `answer_text` text COLLATE utf8mb4_unicode_ci,
  `responder_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `answered_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_aa_question` (`question_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业问答回复表';

/*Table structure for table `assignment_class` */

DROP TABLE IF EXISTS `assignment_class`;

CREATE TABLE `assignment_class` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `assignment_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `class_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_asgn_class` (`assignment_code`,`class_code`),
  KEY `idx_ac_class` (`class_code`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业-班级分配表';

/*Table structure for table `assignment_question` */

DROP TABLE IF EXISTS `assignment_question`;

CREATE TABLE `assignment_question` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `student_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `assignment_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `question_text` text COLLATE utf8mb4_unicode_ci,
  `asked_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_aq_assignment` (`assignment_code`),
  KEY `idx_aq_student` (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业问答表';

/*Table structure for table `assignment_resource` */

DROP TABLE IF EXISTS `assignment_resource`;

CREATE TABLE `assignment_resource` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `assignment_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_url` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `published_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ar_assignment` (`assignment_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业参考资源表';

/*Table structure for table `assignment_submission` */

DROP TABLE IF EXISTS `assignment_submission`;

CREATE TABLE `assignment_submission` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `assignment_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `student_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学生 user_id',
  `answer_content` text COLLATE utf8mb4_unicode_ci,
  `file_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '提交文件 URL',
  `submitted_at` datetime DEFAULT NULL COMMENT '提交时间（NULL=未提交）',
  `teacher_score` decimal(6,2) DEFAULT NULL,
  `teacher_comment` text COLLATE utf8mb4_unicode_ci,
  `graded_at` datetime DEFAULT NULL COMMENT '批阅时间（NULL=未批阅）',
  `grader_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '批阅教师 user_id',
  `is_returned` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否被退回重做',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_as` (`assignment_code`,`student_id`),
  KEY `idx_as_student` (`student_id`),
  KEY `idx_as_submitted` (`submitted_at`),
  KEY `idx_as_graded` (`graded_at`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业提交与批改记录';

/*Table structure for table `cache` */

DROP TABLE IF EXISTS `cache`;

CREATE TABLE `cache` (
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expiration` bigint NOT NULL,
  PRIMARY KEY (`key`),
  KEY `cache_expiration_index` (`expiration`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `cache_locks` */

DROP TABLE IF EXISTS `cache_locks`;

CREATE TABLE `cache_locks` (
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `owner` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expiration` bigint NOT NULL,
  PRIMARY KEY (`key`),
  KEY `cache_locks_expiration_index` (`expiration`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `class_course` */

DROP TABLE IF EXISTS `class_course`;

CREATE TABLE `class_course` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `class_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `term_number` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_class_course` (`class_code`,`course_code`),
  KEY `idx_classcourse_class` (`class_code`),
  KEY `idx_classcourse_course` (`course_code`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `class_group` */

DROP TABLE IF EXISTS `class_group`;

CREATE TABLE `class_group` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `class_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '班级唯一编号',
  `class_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '班级名称',
  `major_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属二级单位编号',
  `enroll_year` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '入学年份',
  `class_desc` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_class_code` (`class_code`),
  KEY `idx_class_major` (`major_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级表（三级单位）';

/*Table structure for table `course` */

DROP TABLE IF EXISTS `course`;

CREATE TABLE `course` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `external_pkg_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `course_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `course_desc` text COLLATE utf8mb4_unicode_ci,
  `course_desc_plain` text COLLATE utf8mb4_unicode_ci,
  `target_audience` text COLLATE utf8mb4_unicode_ci,
  `course_outline` text COLLATE utf8mb4_unicode_ci,
  `cover_image` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `course_type_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creator_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `credit` int NOT NULL DEFAULT '0',
  `study_hours` int NOT NULL DEFAULT '0',
  `training_start` datetime DEFAULT NULL,
  `training_end` datetime DEFAULT NULL,
  `application_area` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `recommend_weight` int NOT NULL DEFAULT '0',
  `is_published` tinyint(1) NOT NULL DEFAULT '1',
  `is_locked` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_course_code` (`course_code`),
  KEY `idx_course_category` (`category_code`),
  KEY `idx_course_creator` (`creator_id`),
  KEY `idx_course_published` (`is_published`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `course_category` */

DROP TABLE IF EXISTS `course_category`;

CREATE TABLE `course_category` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `category_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_locked` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_category_code` (`category_code`),
  KEY `idx_cc_parent` (`parent_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `course_courseware` */

DROP TABLE IF EXISTS `course_courseware`;

CREATE TABLE `course_courseware` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_order` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cc` (`course_code`,`courseware_code`),
  KEY `idx_cc_course` (`course_code`),
  KEY `idx_cc_courseware` (`courseware_code`)
) ENGINE=InnoDB AUTO_INCREMENT=532 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `course_grade` */

DROP TABLE IF EXISTS `course_grade`;

CREATE TABLE `course_grade` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学生 user_id',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课程编号',
  `class_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属班级（冗余，报表用）',
  `position_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源岗位编号（冗余，报表/统计用；岗位分配时写入）',
  `courseware_score` decimal(6,2) DEFAULT NULL COMMENT '课件完成得分',
  `exam_score` decimal(6,2) DEFAULT NULL COMMENT '考试得分（取最高次）',
  `assignment_score` decimal(6,2) DEFAULT NULL COMMENT '作业平均得分',
  `weight_courseware` decimal(4,2) NOT NULL DEFAULT '0.60' COMMENT '课件完成度权重（默认60%）',
  `weight_exam` decimal(4,2) NOT NULL DEFAULT '0.30' COMMENT '考试权重（默认30%）',
  `weight_assignment` decimal(4,2) NOT NULL DEFAULT '0.10' COMMENT '作业权重（默认10%）',
  `total_score` decimal(6,2) DEFAULT NULL COMMENT '综合总分（加权汇总）',
  `grade_rank` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '等级：优/良/中/及格/不及格',
  `total_courseware` int NOT NULL DEFAULT '0' COMMENT '课程总课件数',
  `completed_courseware` int NOT NULL DEFAULT '0' COMMENT '已完成课件数',
  `completion_rate` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '课件完成率（%）',
  `exam_attempt_count` int NOT NULL DEFAULT '0' COMMENT '参加考试次数',
  `assignment_submit_count` int NOT NULL DEFAULT '0' COMMENT '提交作业次数',
  `last_studied_at` datetime DEFAULT NULL,
  `is_passed` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否结业通过',
  `passed_at` datetime DEFAULT NULL COMMENT '结业时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cg` (`user_id`,`course_code`),
  KEY `idx_cg_course` (`course_code`),
  KEY `idx_cg_class` (`class_code`),
  KEY `idx_cg_score` (`total_score`),
  KEY `idx_cg_passed` (`is_passed`),
  KEY `idx_cg_position` (`position_code`),
  KEY `idx_cg_updated_at` (`updated_at`)
) ENGINE=InnoDB AUTO_INCREMENT=202 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程综合成绩（课件完成度+考试+作业加权汇总）';

/*Table structure for table `courseware` */

DROP TABLE IF EXISTS `courseware`;

CREATE TABLE `courseware` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `courseware_key` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tool_key` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `courseware_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `courseware_desc` text COLLATE utf8mb4_unicode_ci,
  `courseware_desc_html` text COLLATE utf8mb4_unicode_ci,
  `type_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `skill_keys` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skill_score_config` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `external_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cover_image` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `media_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vod_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skill_point_count` int NOT NULL DEFAULT '0',
  `page_count` int NOT NULL DEFAULT '0',
  `difficulty_level` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `click_count` int NOT NULL DEFAULT '0',
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creator_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_reviewed` tinyint(1) NOT NULL DEFAULT '0',
  `is_imported` tinyint(1) NOT NULL DEFAULT '0',
  `has_exam` tinyint(1) NOT NULL DEFAULT '0',
  `published_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_courseware_code` (`courseware_code`),
  UNIQUE KEY `uk_courseware_key` (`courseware_key`),
  KEY `idx_cw_type` (`type_code`),
  KEY `idx_cw_creator` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=561 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `courseware_qa` */

DROP TABLE IF EXISTS `courseware_qa`;

CREATE TABLE `courseware_qa` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `qa_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '问题唯一编号',
  `question_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asker_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `asked_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `reply_text` text COLLATE utf8mb4_unicode_ci,
  `replier_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `replied_at` datetime DEFAULT NULL,
  `is_verified` int NOT NULL DEFAULT '0',
  `is_helpful` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cqa_code` (`qa_code`),
  KEY `idx_cqa_course` (`course_code`),
  KEY `idx_cqa_courseware` (`courseware_code`),
  KEY `idx_cqa_asker` (`asker_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课件内站内问答表';

/*Table structure for table `courseware_resource` */

DROP TABLE IF EXISTS `courseware_resource`;

CREATE TABLE `courseware_resource` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `resource_id` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `resource_name` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cr_courseware` (`courseware_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `courseware_study_stats` */

DROP TABLE IF EXISTS `courseware_study_stats`;

CREATE TABLE `courseware_study_stats` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `app_id` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `courseware_key` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `courseware_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_minutes` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '总访问时长',
  `study_minutes` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '有效学习时长',
  `qa_minutes` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '问答时长',
  `stat_date` date DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_css_key_date` (`courseware_key`,`stat_date`)
) ENGINE=InnoDB AUTO_INCREMENT=293 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课件学习时长统计';

/*Table structure for table `courseware_type` */

DROP TABLE IF EXISTS `courseware_type`;

CREATE TABLE `courseware_type` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `type_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `allowed_file_types` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `url_address` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_oc_type` tinyint(1) NOT NULL DEFAULT '0',
  `sort_order` int NOT NULL DEFAULT '0',
  `deleted_at` timestamp NULL DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_type_code` (`type_code`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `curriculum` */

DROP TABLE IF EXISTS `curriculum`;

CREATE TABLE `curriculum` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `curriculum_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学制唯一编号',
  `curriculum_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学制名称',
  `total_terms` int NOT NULL DEFAULT '0' COMMENT '总学期数',
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属机构',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_curriculum_code` (`curriculum_code`),
  KEY `idx_curriculum_org` (`org_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学制表';

/*Table structure for table `curriculum_term` */

DROP TABLE IF EXISTS `curriculum_term`;

CREATE TABLE `curriculum_term` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `curriculum_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属学制编号',
  `term_number` int NOT NULL COMMENT '第几学期',
  `start_at` datetime DEFAULT NULL COMMENT '学期开始时间',
  `end_at` datetime DEFAULT NULL COMMENT '学期结束时间',
  `academic_year` int DEFAULT NULL COMMENT '所属学年',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_term_curriculum` (`curriculum_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学期表';

/*Table structure for table `department` */

DROP TABLE IF EXISTS `department`;

CREATE TABLE `department` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '一级单位唯一编号',
  `dept_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '一级单位名称',
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属机构编号',
  `dept_desc` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dept_code` (`dept_code`),
  KEY `idx_dept_org` (`org_code`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='一级单位/部门表（一级单位）';

/*Table structure for table `dept_benchmark_stats` */

DROP TABLE IF EXISTS `dept_benchmark_stats`;

CREATE TABLE `dept_benchmark_stats` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stat_period` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'month',
  `stat_date` date NOT NULL,
  `avg_completion_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `avg_exam_pass_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `avg_composite_score` decimal(6,2) NOT NULL DEFAULT '0.00',
  `avg_study_minutes` decimal(10,2) NOT NULL DEFAULT '0.00',
  `avg_skill_error_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `avg_engagement_score` decimal(5,2) NOT NULL DEFAULT '0.00',
  `p25_completion_rate` decimal(5,2) DEFAULT NULL,
  `p50_completion_rate` decimal(5,2) DEFAULT NULL,
  `p75_completion_rate` decimal(5,2) DEFAULT NULL,
  `p25_composite_score` decimal(6,2) DEFAULT NULL,
  `p50_composite_score` decimal(6,2) DEFAULT NULL,
  `p75_composite_score` decimal(6,2) DEFAULT NULL,
  `total_learners` int NOT NULL DEFAULT '0',
  `refreshed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dbs` (`dept_code`,`stat_period`,`stat_date`),
  KEY `idx_dbs_org` (`org_code`),
  KEY `idx_dbs_date` (`stat_date`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `exam_answer` */

DROP TABLE IF EXISTS `exam_answer`;

CREATE TABLE `exam_answer` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `enrollment_id` int unsigned NOT NULL COMMENT '关联 exam_enrollment.id',
  `question_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer_content` text COLLATE utf8mb4_unicode_ci COMMENT '作答内容（JSON）',
  `earned_score` decimal(10,2) DEFAULT NULL COMMENT '得分',
  `grading_status` tinyint NOT NULL DEFAULT '0' COMMENT '0=未批 1=已批',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ea_enrollment` (`enrollment_id`),
  KEY `idx_ea_question` (`question_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='答题结果表';

/*Table structure for table `exam_enrollment` */

DROP TABLE IF EXISTS `exam_enrollment`;

CREATE TABLE `exam_enrollment` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `exam_session_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '考场编号',
  `user_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '考生编号',
  `assigned_paper_key` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已抽取试卷 Key',
  `started_at` datetime DEFAULT NULL COMMENT '开始答题时间',
  `submitted_at` datetime DEFAULT NULL COMMENT '交卷时间',
  `last_saved_at` datetime DEFAULT NULL COMMENT '最后暂存时间',
  `remaining_seconds` int DEFAULT NULL COMMENT '剩余时间（秒）',
  `total_score` decimal(10,2) DEFAULT NULL COMMENT '总成绩',
  `is_graded` tinyint(1) NOT NULL DEFAULT '0',
  `result_published` tinyint(1) NOT NULL DEFAULT '0',
  `attempt_number` int NOT NULL DEFAULT '0' COMMENT '第几次考试',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ee_session` (`exam_session_code`),
  KEY `idx_ee_user` (`user_code`),
  KEY `idx_ee_session_user` (`exam_session_code`,`user_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考生报名/考试记录表';

/*Table structure for table `exam_paper` */

DROP TABLE IF EXISTS `exam_paper`;

CREATE TABLE `exam_paper` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `paper_key` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '试卷唯一 Key',
  `paper_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `paper_desc` text COLLATE utf8mb4_unicode_ci,
  `attachment_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `type_count_config` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '各题型数量（JSON）',
  `type_score_config` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '各题型分值（JSON）',
  `creator_id` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_code` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `use_weighted_score` tinyint(1) NOT NULL DEFAULT '0',
  `sort_order` int NOT NULL DEFAULT '0',
  `is_free` tinyint(1) NOT NULL DEFAULT '0',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '0=草稿 1=发布',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_paper_key` (`paper_key`),
  KEY `idx_ep_org` (`dept_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试卷表';

/*Table structure for table `exam_paper_pool` */

DROP TABLE IF EXISTS `exam_paper_pool`;

CREATE TABLE `exam_paper_pool` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `exam_session_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `paper_key` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_epp` (`exam_session_code`,`paper_key`),
  KEY `idx_epp_session` (`exam_session_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考场-试卷池关联表';

/*Table structure for table `exam_session` */

DROP TABLE IF EXISTS `exam_session`;

CREATE TABLE `exam_session` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `exam_session_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '考场唯一编号',
  `session_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '考场名称',
  `session_desc` text COLLATE utf8mb4_unicode_ci,
  `exam_notice` text COLLATE utf8mb4_unicode_ci COMMENT '考场须知',
  `open_at` datetime DEFAULT NULL COMMENT '开放开始时间（NULL=不限）',
  `close_at` datetime DEFAULT NULL COMMENT '开放结束时间',
  `time_limit_seconds` int NOT NULL DEFAULT '0' COMMENT '时限: 0=不限 >0=秒 -1=固定时间段',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '0未开始 1进行中 2已终止 3已停用',
  `auto_publish_result` tinyint(1) NOT NULL DEFAULT '0',
  `max_attempts` int NOT NULL DEFAULT '0' COMMENT '最大考试次数（0=不限）',
  `linked_course_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联课程',
  `type_count_config` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `type_score_config` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `grading_mode` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0=自动 1=人工',
  `creator_id` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_code` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `competition_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `use_random_questions` tinyint(1) NOT NULL DEFAULT '0',
  `is_open_enrollment` tinyint(1) NOT NULL DEFAULT '0' COMMENT '学生可自主报名',
  `is_stopped` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_exam_session_code` (`exam_session_code`),
  KEY `idx_es_org` (`dept_code`),
  KEY `idx_es_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考试场次（考场）';

/*Table structure for table `failed_jobs` */

DROP TABLE IF EXISTS `failed_jobs`;

CREATE TABLE `failed_jobs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `uuid` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `connection` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `queue` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `exception` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `failed_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `failed_jobs_uuid_unique` (`uuid`),
  KEY `failed_jobs_connection_queue_failed_at_index` (`connection`,`queue`,`failed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `feature` */

DROP TABLE IF EXISTS `feature`;

CREATE TABLE `feature` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `feature_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '功能名称',
  `feature_icon` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图标资源路径',
  `parent_id` int unsigned NOT NULL DEFAULT '0' COMMENT '父节点 ID（0 为顶级）',
  `feature_desc` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '功能描述',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序权重（越大越靠前）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_feature_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='功能权限定义表';

/*Table structure for table `job_batches` */

DROP TABLE IF EXISTS `job_batches`;

CREATE TABLE `job_batches` (
  `id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_jobs` int NOT NULL,
  `pending_jobs` int NOT NULL,
  `failed_jobs` int NOT NULL,
  `failed_job_ids` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `options` mediumtext COLLATE utf8mb4_unicode_ci,
  `cancelled_at` int DEFAULT NULL,
  `created_at` int NOT NULL,
  `finished_at` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `jobs` */

DROP TABLE IF EXISTS `jobs`;

CREATE TABLE `jobs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `queue` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `attempts` smallint unsigned NOT NULL,
  `reserved_at` int unsigned DEFAULT NULL,
  `available_at` int unsigned NOT NULL,
  `created_at` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `jobs_queue_index` (`queue`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `learner_profile` */

DROP TABLE IF EXISTS `learner_profile`;

CREATE TABLE `learner_profile` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学习者 user_id',
  `avg_session_minutes` int NOT NULL DEFAULT '0' COMMENT '平均单次学习时长（分钟）',
  `preferred_time_slots` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '偏好时段（JSON: {morning:0.4, evening:0.6}）',
  `avg_weekly_study_days` decimal(4,2) NOT NULL DEFAULT '0.00' COMMENT '周均学习天数',
  `avg_completion_rate` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '课件平均完成率（%）',
  `total_study_minutes` int NOT NULL DEFAULT '0' COMMENT '累计学习总时长（分钟）',
  `total_courses_completed` int NOT NULL DEFAULT '0' COMMENT '已完成课程数',
  `skill_scores` json DEFAULT NULL COMMENT '技能点掌握情况 {courseware_key: {step:score}}',
  `strong_domains` text COLLATE utf8mb4_unicode_ci COMMENT '擅长领域（JSON 数组）',
  `weak_domains` text COLLATE utf8mb4_unicode_ci COMMENT '薄弱领域（JSON 数组）',
  `avg_skill_error_rate` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '技能点平均出错率（%）',
  `learning_style` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'visual / reading / kinesthetic',
  `study_pace` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'fast / steady / slow',
  `engagement_score` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '参与度评分（0-100）',
  `profile_summary` text COLLATE utf8mb4_unicode_ci COMMENT 'LLM 生成的自然语言学习画像摘要',
  `summary_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '画像版本号（对应 ai_learning_plan.id）',
  `profile_built_at` datetime DEFAULT NULL COMMENT '画像最后聚合时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_lpr_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习者画像（定期聚合，作为 LLM 规划的 Context 数据源）';

/*Table structure for table `learning_path` */

DROP TABLE IF EXISTS `learning_path`;

CREATE TABLE `learning_path` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `path_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '路径唯一编号',
  `path_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '路径名称',
  `path_desc` text COLLATE utf8mb4_unicode_ci COMMENT '路径描述',
  `target_position` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标岗位/角色',
  `target_skills` text COLLATE utf8mb4_unicode_ci COMMENT '目标技能集（JSON 数组）',
  `source_type` tinyint NOT NULL DEFAULT '0' COMMENT '来源: 0=手动 1=AI生成 2=AI优化迭代',
  `creator_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '创建者 user_id（手动创建时）',
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_template` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为可复用模板',
  `estimated_days` int DEFAULT NULL COMMENT '预计完成总天数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_path_code` (`path_code`),
  KEY `idx_lpath_org` (`org_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习路径定义表';

/*Table structure for table `learning_progress` */

DROP TABLE IF EXISTS `learning_progress`;

CREATE TABLE `learning_progress` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课程编号',
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课件编号',
  `type_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '课件类型代码（冗余，免 JOIN，关联 courseware_type.type_code）',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '0=未开始 1=学习中 2=已完成',
  `best_score` decimal(6,2) DEFAULT NULL COMMENT '历史最高得分',
  `last_score` decimal(6,2) DEFAULT NULL COMMENT '最近一次得分',
  `total_study_minutes` int NOT NULL DEFAULT '0' COMMENT '累计学习时长（分钟）',
  `attempt_count` int NOT NULL DEFAULT '0' COMMENT '学习/尝试次数',
  `first_started_at` datetime DEFAULT NULL COMMENT '首次开始学习时间',
  `last_studied_at` datetime DEFAULT NULL COMMENT '最近学习时间',
  `completed_at` datetime DEFAULT NULL COMMENT '完成时间',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_lp` (`user_id`,`course_code`,`courseware_code`),
  KEY `idx_lp_user_course` (`user_id`,`course_code`),
  KEY `idx_lp_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=202 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习进度快照（学生×课程×课件，异步更新）';

/*Table structure for table `login_log` */

DROP TABLE IF EXISTS `login_log`;

CREATE TABLE `login_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID',
  `logged_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IPv4/IPv6',
  `device_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备类型',
  `token` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登录令牌',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_login_user` (`user_id`),
  KEY `idx_login_time` (`logged_at`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户登录日志';

/*Table structure for table `major` */

DROP TABLE IF EXISTS `major`;

CREATE TABLE `major` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `major_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '二级单位唯一编号',
  `major_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '二级单位名称',
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属一级单位编号',
  `major_desc` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `curriculum_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联学制编号',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_major_code` (`major_code`),
  KEY `idx_major_dept` (`dept_code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='二级单位表（二级单位）';

/*Table structure for table `migrations` */

DROP TABLE IF EXISTS `migrations`;

CREATE TABLE `migrations` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `migration` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `batch` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `org` */

DROP TABLE IF EXISTS `org`;

CREATE TABLE `org` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '机构唯一编号',
  `app_id` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台应用 ID',
  `org_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '机构名称',
  `org_desc` text COLLATE utf8mb4_unicode_ci COMMENT '机构描述',
  `is_default` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否默认机构',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_org_code` (`org_code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='机构/学校表';

/*Table structure for table `org_benchmark_stats` */

DROP TABLE IF EXISTS `org_benchmark_stats`;

CREATE TABLE `org_benchmark_stats` (
  `id` int NOT NULL AUTO_INCREMENT,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stat_period` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'month',
  `stat_date` date NOT NULL,
  `avg_completion_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `avg_exam_pass_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `avg_composite_score` decimal(6,2) NOT NULL DEFAULT '0.00',
  `avg_study_minutes` decimal(10,2) NOT NULL DEFAULT '0.00',
  `avg_skill_error_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `avg_engagement_score` decimal(5,2) NOT NULL DEFAULT '0.00',
  `p25_completion_rate` decimal(5,2) DEFAULT NULL,
  `p50_completion_rate` decimal(5,2) DEFAULT NULL,
  `p75_completion_rate` decimal(5,2) DEFAULT NULL,
  `p25_composite_score` decimal(6,2) DEFAULT NULL,
  `p50_composite_score` decimal(6,2) DEFAULT NULL,
  `p75_composite_score` decimal(6,2) DEFAULT NULL,
  `total_orgs` int NOT NULL DEFAULT '0',
  `total_learners` int NOT NULL DEFAULT '0',
  `refreshed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_obs` (`org_code`,`stat_period`,`stat_date`),
  KEY `idx_obs_date` (`stat_date`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `org_course_stats` */

DROP TABLE IF EXISTS `org_course_stats`;

CREATE TABLE `org_course_stats` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stat_date` date NOT NULL,
  `total_study_minutes` decimal(12,2) NOT NULL DEFAULT '0.00',
  `completions` int NOT NULL DEFAULT '0' COMMENT '完成人次',
  `active_learners` int NOT NULL DEFAULT '0' COMMENT '活跃人数（去重）',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ocs` (`org_code`,`course_code`,`stat_date`),
  KEY `idx_ocs_org_date` (`org_code`,`stat_date`)
) ENGINE=InnoDB AUTO_INCREMENT=381 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='机构-课程日统计';

/*Table structure for table `org_daily_stats` */

DROP TABLE IF EXISTS `org_daily_stats`;

CREATE TABLE `org_daily_stats` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stat_date` date NOT NULL COMMENT '统计日期',
  `study_sessions` int NOT NULL DEFAULT '0' COMMENT '当日学习人次',
  `total_study_minutes` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '学习总时长（分钟）',
  `courseware_completed` int NOT NULL DEFAULT '0' COMMENT '课件完成数',
  `skill_points_completed` int NOT NULL DEFAULT '0' COMMENT '技能点完成数',
  `exam_completed` int NOT NULL DEFAULT '0' COMMENT '考试完成人次',
  `experiment_minutes` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '实操实验时长（分钟）',
  `qa_asked` int NOT NULL DEFAULT '0' COMMENT '提问数',
  `qa_answered` int NOT NULL DEFAULT '0' COMMENT '回答数',
  `active_users` int NOT NULL DEFAULT '0' COMMENT '活跃用户数（去重）',
  `login_times` int NOT NULL DEFAULT '0' COMMENT '登录总次数',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ods` (`org_code`,`stat_date`),
  KEY `idx_ods_date` (`stat_date`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='机构日统计汇总';

/*Table structure for table `org_monthly_stats` */

DROP TABLE IF EXISTS `org_monthly_stats`;

CREATE TABLE `org_monthly_stats` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stat_month` date NOT NULL COMMENT '统计月份（取当月 1 日存储）',
  `total_study_minutes` int NOT NULL DEFAULT '0',
  `total_study_sessions` int NOT NULL DEFAULT '0',
  `active_users` int NOT NULL DEFAULT '0',
  `avg_study_minutes` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '人均学习时长',
  `avg_study_sessions` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '人均学习次数',
  `avg_courseware_done` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '人均完成课件数',
  `avg_skill_points_done` decimal(10,2) NOT NULL DEFAULT '0.00',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_oms` (`org_code`,`stat_month`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='机构月统计汇总';

/*Table structure for table `paper_attachment` */

DROP TABLE IF EXISTS `paper_attachment`;

CREATE TABLE `paper_attachment` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `paper_key` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `file_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pa_paper` (`paper_key`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试卷附件表';

/*Table structure for table `paper_question` */

DROP TABLE IF EXISTS `paper_question`;

CREATE TABLE `paper_question` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `paper_key` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `question_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type_code` char(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score_config` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pq_paper` (`paper_key`),
  KEY `idx_pq_question` (`question_code`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试卷-试题关联表';

/*Table structure for table `password_reset_tokens` */

DROP TABLE IF EXISTS `password_reset_tokens`;

CREATE TABLE `password_reset_tokens` (
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `token` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `path_enrollment` */

DROP TABLE IF EXISTS `path_enrollment`;

CREATE TABLE `path_enrollment` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学习者 user_id',
  `path_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '路径编号',
  `current_node_seq` int NOT NULL DEFAULT '1' COMMENT '当前所在节点序号',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '0=进行中 1=已完成 2=已放弃',
  `overall_progress` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '整体完成率（%）',
  `enrolled_at` datetime DEFAULT NULL COMMENT '注册/开始时间',
  `ai_predicted_done` datetime DEFAULT NULL COMMENT 'AI 动态预测完成时间',
  `completed_at` datetime DEFAULT NULL,
  `last_ai_planned_at` datetime DEFAULT NULL COMMENT '最后一次 AI 重规划时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pe` (`user_id`,`path_code`),
  KEY `idx_pe_user` (`user_id`),
  KEY `idx_pe_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户路径注册与进度表';

/*Table structure for table `path_node` */

DROP TABLE IF EXISTS `path_node`;

CREATE TABLE `path_node` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `path_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属路径编号',
  `node_seq` int NOT NULL COMMENT '节点顺序（从1开始）',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联课程编号',
  `node_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '节点展示名（默认取课程名）',
  `is_mandatory` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否必修',
  `unlock_condition` text COLLATE utf8mb4_unicode_ci COMMENT '解锁条件（JSON: 前置节点seq + 最低通过分数）',
  `estimated_days` int DEFAULT NULL COMMENT '该节点预计学习天数',
  `ai_recommend_reason` text COLLATE utf8mb4_unicode_ci COMMENT 'AI 推荐理由（展示给学习者）',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pn` (`path_code`,`node_seq`),
  KEY `idx_pn_path` (`path_code`),
  KEY `idx_pn_course` (`course_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='路径节点（路径课程序列）';

/*Table structure for table `personal_access_tokens` */

DROP TABLE IF EXISTS `personal_access_tokens`;

CREATE TABLE `personal_access_tokens` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `tokenable_type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tokenable_id` bigint unsigned NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `token` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `abilities` text COLLATE utf8mb4_unicode_ci,
  `last_used_at` timestamp NULL DEFAULT NULL,
  `expires_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `personal_access_tokens_token_unique` (`token`),
  KEY `personal_access_tokens_tokenable_type_tokenable_id_index` (`tokenable_type`,`tokenable_id`),
  KEY `personal_access_tokens_expires_at_index` (`expires_at`)
) ENGINE=InnoDB AUTO_INCREMENT=110 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `platform_qa` */

DROP TABLE IF EXISTS `platform_qa`;

CREATE TABLE `platform_qa` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `qa_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '问题唯一编号',
  `app_key` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源应用 Key',
  `openid` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '微信/第三方 OpenID',
  `asker_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '提问用户 ID',
  `question_text` text COLLATE utf8mb4_unicode_ci,
  `courseware_key` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联课件 Key',
  `courseware_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `courseware_step` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '课件步骤/页面',
  `qa_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '问题类型',
  `skill_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pkg_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `point_cost` int NOT NULL DEFAULT '0' COMMENT '消费积分',
  `asked_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `reply_text` text COLLATE utf8mb4_unicode_ci,
  `replied_at` datetime DEFAULT NULL,
  `read_at` datetime DEFAULT NULL,
  `rating` int NOT NULL DEFAULT '0' COMMENT '0=未评 1=有帮助 -1=无帮助',
  `state` tinyint NOT NULL DEFAULT '0' COMMENT '0=待回答 1=已回答 2=已读归档',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_qa_code` (`qa_code`),
  KEY `idx_pqa_asker` (`asker_id`),
  KEY `idx_pqa_app` (`app_key`),
  KEY `idx_pqa_state` (`state`),
  KEY `idx_pqa_asked` (`asked_at`),
  KEY `idx_pqa_courseware` (`courseware_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台问答统一表（替代旧版三表状态机）';

/*Table structure for table `position` */

DROP TABLE IF EXISTS `position`;

CREATE TABLE `position` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `position_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '岗位唯一编号',
  `position_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '岗位名称',
  `position_desc` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '岗位描述',
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属机构编号（多租户隔离，始终必填）',
  `scope_type` tinyint NOT NULL DEFAULT '0' COMMENT '岗位归属层级: 0=机构 1=一级单位 2=二级单位 3=班级',
  `scope_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对应层级编号（org/dept/major/class_code）',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序权重',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_position_code` (`position_code`),
  UNIQUE KEY `uk_position_scope_name` (`scope_type`,`scope_code`,`position_name`),
  KEY `idx_position_org` (`org_code`),
  KEY `idx_position_scope` (`scope_type`,`scope_code`),
  CONSTRAINT `chk_position_scope_type` CHECK ((`scope_type` in (0,1,2,3)))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗位表（scope_type+scope_code 多态引用，支持机构/一级/二级/班级四级归属）';

/*Table structure for table `position_course` */

DROP TABLE IF EXISTS `position_course`;

CREATE TABLE `position_course` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `position_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '岗位编号（关联 position.position_code）',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课程编号（关联 course.course_code）',
  `is_required` tinyint(1) NOT NULL DEFAULT '1' COMMENT '1=必修 0=选修',
  `deadline` datetime DEFAULT NULL COMMENT '完成截止时间（NULL=不限）',
  `assigned_by` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分配操作人 user_id',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_position_course` (`position_code`,`course_code`),
  KEY `idx_pc_position` (`position_code`),
  KEY `idx_pc_course` (`course_code`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗位-课程分配表（岗位维度批量分配课程）';

/*Table structure for table `push_device` */

DROP TABLE IF EXISTS `push_device`;

CREATE TABLE `push_device` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID',
  `channel_id` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '推送渠道唯一 ID',
  `device_token` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备标识',
  `push_platform` tinyint NOT NULL COMMENT '1=华为 2=小米 3=信鸽 4=自定义',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pd_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户推送设备绑定表';

/*Table structure for table `push_notification_log` */

DROP TABLE IF EXISTS `push_notification_log`;

CREATE TABLE `push_notification_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '接收用户',
  `platform` tinyint NOT NULL COMMENT '平台: 1=华为 2=小米 3=信鸽 4=自定义',
  `message_title` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message_body` text COLLATE utf8mb4_unicode_ci,
  `biz_type` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '业务类型: qa_reply/assignment/exam...',
  `biz_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '业务编号（便于排查）',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '0=待发 1=成功 2=失败',
  `fail_reason` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `retry_count` int NOT NULL DEFAULT '0',
  `sent_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pnl_user` (`user_id`),
  KEY `idx_pnl_status` (`status`),
  KEY `idx_pnl_biz` (`biz_type`,`biz_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `qa_question_type` */

DROP TABLE IF EXISTS `qa_question_type`;

CREATE TABLE `qa_question_type` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `type_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '类型唯一标识',
  `type_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `auto_reply` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否自动回复',
  `auto_reply_msg` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_qat_type` (`type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问题类型定义表';

/*Table structure for table `qa_session_log` */

DROP TABLE IF EXISTS `qa_session_log`;

CREATE TABLE `qa_session_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `session_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `intent` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `complexity` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modules_used` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `steps_count` int DEFAULT '0',
  `tools_used` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `duration_ms` int DEFAULT NULL,
  `total_tokens` int DEFAULT NULL,
  `user_feedback` smallint DEFAULT NULL,
  `fallback_used` tinyint(1) DEFAULT '0',
  `asked_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_qsl_asked` (`asked_at`),
  KEY `idx_qsl_intent` (`intent`),
  KEY `idx_qsl_feedback` (`user_feedback`)
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `qa_voice` */

DROP TABLE IF EXISTS `qa_voice`;

CREATE TABLE `qa_voice` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `qa_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联 platform_qa.qa_code',
  `question_voice_url` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '提问语音 URL',
  `question_duration` int NOT NULL DEFAULT '0',
  `reply_voice_url` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '回复语音 URL',
  `reply_duration` int NOT NULL DEFAULT '0',
  `state` tinyint NOT NULL DEFAULT '0' COMMENT '0=仅提问 1=已有回复 2=已归档',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_qav_qa` (`qa_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答语音附件表';

/*Table structure for table `qa_vote_log` */

DROP TABLE IF EXISTS `qa_vote_log`;

CREATE TABLE `qa_vote_log` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `app_id` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `qa_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vote_type` tinyint NOT NULL COMMENT '1=点赞 2=点踩',
  `voted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_qvl_qa` (`qa_code`),
  KEY `idx_qvl_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答点赞/点踩日志';

/*Table structure for table `question` */

DROP TABLE IF EXISTS `question`;

CREATE TABLE `question` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `question_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '试题唯一编号',
  `type_code` char(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '题型编码',
  `question_content` longtext COLLATE utf8mb4_unicode_ci COMMENT '题目内容（HTML）',
  `content_plain` text COLLATE utf8mb4_unicode_ci COMMENT '纯文本内容（搜索用）',
  `keyword_tags` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关键词标签',
  `difficulty_level` int NOT NULL DEFAULT '0' COMMENT '难度等级（1-5）',
  `grading_type` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0=自动评分 1=人工评分',
  `knowledge_point` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '知识点',
  `related_course_key` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联课程 Key',
  `attachment_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '附件 URL',
  `creator_id` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_code` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_disabled` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否停用',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_question_code` (`question_code`),
  KEY `idx_q_type` (`type_code`),
  KEY `idx_q_org` (`dept_code`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题库';

/*Table structure for table `question_attachment` */

DROP TABLE IF EXISTS `question_attachment`;

CREATE TABLE `question_attachment` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `question_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_qa_question` (`question_code`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试题附件表';

/*Table structure for table `question_option` */

DROP TABLE IF EXISTS `question_option`;

CREATE TABLE `question_option` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `option_index` int NOT NULL COMMENT '选项序号（A=1 B=2...）',
  `question_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `option_content` text COLLATE utf8mb4_unicode_ci COMMENT '选项内容',
  `is_correct` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否正确答案',
  `error_min` decimal(18,2) DEFAULT NULL COMMENT '误差下限（数值填空）',
  `error_max` decimal(18,2) DEFAULT NULL COMMENT '误差上限（数值填空）',
  `use_error_range` tinyint(1) NOT NULL DEFAULT '0',
  `correct_count` int NOT NULL DEFAULT '0' COMMENT '答对次数',
  `total_count` int NOT NULL DEFAULT '0' COMMENT '作答次数',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_qo_question` (`question_code`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试题选项/答案表';

/*Table structure for table `question_option_img` */

DROP TABLE IF EXISTS `question_option_img`;

CREATE TABLE `question_option_img` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `option_index` int NOT NULL,
  `question_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_qoi_question` (`question_code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试题选项图片表';

/*Table structure for table `question_type` */

DROP TABLE IF EXISTS `question_type`;

CREATE TABLE `question_type` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `type_code` char(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '题型编码',
  `type_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '题型名称',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_qt_code` (`type_code`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考试题型字典';

/*Table structure for table `role` */

DROP TABLE IF EXISTS `role`;

CREATE TABLE `role` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `role_level` tinyint NOT NULL COMMENT '角色等级: 0超管/1管理员/2教师/3学生',
  `role_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色名称',
  `role_desc` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '角色描述',
  `is_hardcoded` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否硬编码角色（1=超管，权限不走数据库）',
  `is_hidden` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否在前端隐藏',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_level` (`role_level`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

/*Table structure for table `role_permission` */

DROP TABLE IF EXISTS `role_permission`;

CREATE TABLE `role_permission` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `role_level` tinyint NOT NULL COMMENT '角色等级（禁止填 0）',
  `feature_id` int unsigned NOT NULL COMMENT '功能权限 ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rp` (`role_level`,`feature_id`),
  KEY `idx_rp_role` (`role_level`),
  CONSTRAINT `chk_no_superadmin_permission` CHECK ((`role_level` <> 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色-权限关联表（role_level=0 由 CHECK 约束禁止写入）';

/*Table structure for table `sessions` */

DROP TABLE IF EXISTS `sessions`;

CREATE TABLE `sessions` (
  `id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` bigint unsigned DEFAULT NULL,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` text COLLATE utf8mb4_unicode_ci,
  `payload` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_activity` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `sessions_user_id_index` (`user_id`),
  KEY `sessions_last_activity_index` (`last_activity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `skill_error_log` */

DROP TABLE IF EXISTS `skill_error_log`;

CREATE TABLE `skill_error_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID',
  `user_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `step_index` int DEFAULT NULL COMMENT '技能点步骤序号',
  `step_score` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `error_count` int NOT NULL DEFAULT '0',
  `occurred_at` datetime NOT NULL COMMENT '发生时间（分区键，禁止 NULL）',
  `client_stamp` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`,`occurred_at`),
  KEY `idx_sel_user` (`user_id`),
  KEY `idx_sel_courseware` (`courseware_code`),
  KEY `idx_sel_time` (`occurred_at`)
) ENGINE=InnoDB AUTO_INCREMENT=201 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技能点错误日志（按年 Range 分区）'
/*!50100 PARTITION BY RANGE (year(`occurred_at`))
(PARTITION p2021 VALUES LESS THAN (2022) ENGINE = InnoDB,
 PARTITION p2022 VALUES LESS THAN (2023) ENGINE = InnoDB,
 PARTITION p2023 VALUES LESS THAN (2024) ENGINE = InnoDB,
 PARTITION p2024 VALUES LESS THAN (2025) ENGINE = InnoDB,
 PARTITION p2025 VALUES LESS THAN (2026) ENGINE = InnoDB,
 PARTITION p2026 VALUES LESS THAN (2027) ENGINE = InnoDB,
 PARTITION p_future VALUES LESS THAN MAXVALUE ENGINE = InnoDB) */;

/*Table structure for table `skill_point` */

DROP TABLE IF EXISTS `skill_point`;

CREATE TABLE `skill_point` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `courseware_key` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `step_index` int NOT NULL,
  `score_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score_config` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sp` (`courseware_key`,`step_index`),
  KEY `idx_sp_key` (`courseware_key`)
) ENGINE=InnoDB AUTO_INCREMENT=1487 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `skill_point_log` */

DROP TABLE IF EXISTS `skill_point_log`;

CREATE TABLE `skill_point_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID',
  `user_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `courseware_key` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '课件 Key',
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课件编号',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '课程编号',
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skills_count` int DEFAULT NULL COMMENT '技能点步骤序号',
  `step_score` text COLLATE utf8mb4_unicode_ci,
  `correct_count` int NOT NULL DEFAULT '0' COMMENT '正确操作次数',
  `error_count` int NOT NULL DEFAULT '0' COMMENT '错误操作次数',
  `is_correct` tinyint(1) NOT NULL DEFAULT '0' COMMENT '本次操作是否正确',
  `operated_at` datetime DEFAULT NULL COMMENT '操作时间',
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_spl_user` (`user_id`),
  KEY `idx_spl_courseware` (`courseware_code`),
  KEY `idx_spl_user_cw_course` (`user_id`,`courseware_code`,`course_code`)
) ENGINE=InnoDB AUTO_INCREMENT=209 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技能点操作日志（细粒度）';

/*Table structure for table `student_class` */

DROP TABLE IF EXISTS `student_class`;

CREATE TABLE `student_class` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学生 user_id',
  `class_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属班级编号',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_student_user` (`user_id`),
  KEY `idx_sc_class` (`class_code`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生-班级归属表（1:1）';

/*Table structure for table `study_session_log` */

DROP TABLE IF EXISTS `study_session_log`;

CREATE TABLE `study_session_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID',
  `user_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户编号（冗余）',
  `courseware_key` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课件 Key',
  `courseware_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '课件名称（冗余）',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '课程编号',
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '一级单位编号',
  `session_score` decimal(6,2) DEFAULT NULL COMMENT '本次得分（满分100）',
  `skill_scores` text COLLATE utf8mb4_unicode_ci,
  `skills_count` int NOT NULL DEFAULT '0' COMMENT '附加得分',
  `started_at` datetime DEFAULT NULL COMMENT '开始时间',
  `stopped_at` datetime DEFAULT NULL COMMENT '结束时间（NULL=学习中）',
  `error_count` int NOT NULL DEFAULT '0' COMMENT '错误操作次数',
  `client_stamp` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端时间戳（防重复提交）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ssl_user` (`user_id`),
  KEY `idx_ssl_courseware` (`courseware_key`),
  KEY `idx_ssl_course` (`course_code`),
  KEY `idx_ssl_started` (`started_at`),
  KEY `idx_ssl_user_cw_course` (`user_id`,`courseware_key`,`course_code`)
) ENGINE=InnoDB AUTO_INCREMENT=286 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习会话日志（每次学习汇总）';

/*Table structure for table `teacher_class` */

DROP TABLE IF EXISTS `teacher_class`;

CREATE TABLE `teacher_class` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '教师 user_id',
  `class_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '班级编号',
  `role_type` tinyint NOT NULL DEFAULT '1' COMMENT '0=班主任 1=任课教师 2=辅导教师',
  `subject` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '任课科目',
  `assigned_by` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分配操作人',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_teacher_class_role` (`user_id`,`class_code`,`role_type`),
  KEY `idx_tc_user` (`user_id`),
  KEY `idx_tc_class` (`class_code`),
  KEY `idx_tc_role` (`role_type`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `teacher_dept` */

DROP TABLE IF EXISTS `teacher_dept`;

CREATE TABLE `teacher_dept` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '教师 user_id',
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属一级单位编号',
  `role_type` tinyint NOT NULL DEFAULT '0' COMMENT '角色: 0=主讲 1=辅导',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_td` (`user_id`,`dept_code`),
  KEY `idx_td_dept` (`dept_code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师-一级单位归属关联表';

/*Table structure for table `user_course` */

DROP TABLE IF EXISTS `user_course`;

CREATE TABLE `user_course` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID',
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课程编号',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_course` (`user_id`,`course_code`),
  KEY `idx_uc_user` (`user_id`),
  KEY `idx_uc_course` (`course_code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户-课程个人分配表';

/*Table structure for table `user_course_auth` */

DROP TABLE IF EXISTS `user_course_auth`;

CREATE TABLE `user_course_auth` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `external_pkg_code` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `authid` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_pkg` (`user_code`,`external_pkg_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `user_info` */

DROP TABLE IF EXISTS `user_info`;

CREATE TABLE `user_info` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '系统唯一用户标识（UUID）',
  `user_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '工号/学号（业务编号）',
  `user_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户姓名',
  `mobile` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号',
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希（bcrypt/argon2）',
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
  `role_level` tinyint NOT NULL DEFAULT '3' COMMENT '角色等级',
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '主归属一级单位编号（学生必填；教师的多部门归属以 teacher_dept 为准）',
  `remember_token` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `position_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '岗位编号',
  `external_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '第三方/外部系统编号',
  `min_login_times` int NOT NULL DEFAULT '0' COMMENT '要求最低登录次数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  UNIQUE KEY `uk_user_code` (`user_code`),
  KEY `idx_ui_role` (`role_level`),
  KEY `idx_ui_mobile` (`mobile`),
  KEY `idx_ui_dept` (`dept_code`)
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='核心用户表';

/*Table structure for table `user_profile` */

DROP TABLE IF EXISTS `user_profile`;

CREATE TABLE `user_profile` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联 user_info.user_id',
  `gender` tinyint DEFAULT NULL COMMENT '性别: 1=男 2=女',
  `education` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学历',
  `phone` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '固定电话',
  `region` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所在地区',
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '详细地址',
  `industry` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '行业',
  `job_title` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '职务',
  `position_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '岗位编号',
  `birthday` date DEFAULT NULL COMMENT '出生日期',
  `id_number` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '身份证号',
  `avatar_url` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像 URL',
  `last_login_at` datetime DEFAULT NULL COMMENT '最后登录时间',
  `biography` text COLLATE utf8mb4_unicode_ci COMMENT '个人简介',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_up_user` (`user_id`),
  KEY `idx_up_position_code` (`position_code`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户扩展信息表';

/*Table structure for table `users` */

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email_verified_at` timestamp NULL DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `remember_token` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_email_unique` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `v_exam_analysis` */

DROP TABLE IF EXISTS `v_exam_analysis`;

CREATE TABLE `v_exam_analysis` (
  `id` int NOT NULL AUTO_INCREMENT,
  `exam_session_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `open_at` datetime DEFAULT NULL,
  `close_at` datetime DEFAULT NULL,
  `linked_course_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `attempt_number` int NOT NULL DEFAULT '0',
  `total_score` decimal(10,2) DEFAULT NULL,
  `is_passed` tinyint(1) DEFAULT NULL,
  `is_graded` tinyint(1) NOT NULL DEFAULT '0',
  `submitted_at` datetime DEFAULT NULL,
  `duration_seconds` int DEFAULT NULL,
  `type_scores` json DEFAULT NULL,
  `correct_count` int DEFAULT NULL,
  `total_questions` int DEFAULT NULL,
  `accuracy_rate` decimal(5,2) DEFAULT NULL,
  `refreshed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_vea_session` (`exam_session_code`),
  KEY `idx_vea_user` (`user_code`),
  KEY `idx_vea_course` (`linked_course_code`),
  KEY `idx_vea_open_at` (`open_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `v_learner_comprehensive` */

DROP TABLE IF EXISTS `v_learner_comprehensive`;

CREATE TABLE `v_learner_comprehensive` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `org_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `class_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `class_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_courses` int NOT NULL DEFAULT '0',
  `courses_completed` int NOT NULL DEFAULT '0',
  `completion_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `avg_composite_score` decimal(6,2) DEFAULT NULL,
  `avg_courseware_score` decimal(6,2) DEFAULT NULL,
  `avg_exam_score` decimal(6,2) DEFAULT NULL,
  `avg_assignment_score` decimal(6,2) DEFAULT NULL,
  `grade_rank` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_exams_taken` int NOT NULL DEFAULT '0',
  `exams_passed` int NOT NULL DEFAULT '0',
  `exam_pass_rate` decimal(5,2) DEFAULT NULL,
  `best_exam_score` decimal(10,2) DEFAULT NULL,
  `total_study_minutes` int NOT NULL DEFAULT '0',
  `total_study_sessions` int NOT NULL DEFAULT '0',
  `avg_session_minutes` int DEFAULT NULL,
  `last_studied_at` datetime DEFAULT NULL,
  `is_at_risk` tinyint(1) NOT NULL DEFAULT '0',
  `risk_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `days_since_last_study` int DEFAULT NULL,
  `refreshed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_vlc` (`user_id`),
  KEY `idx_vlc_dept` (`dept_code`),
  KEY `idx_vlc_org` (`org_code`),
  KEY `idx_vlc_risk` (`is_at_risk`,`risk_type`)
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `v_skill_error_summary` */

DROP TABLE IF EXISTS `v_skill_error_summary`;

CREATE TABLE `v_skill_error_summary` (
  `id` int NOT NULL AUTO_INCREMENT,
  `courseware_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `courseware_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `course_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_code` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `step_index` int NOT NULL,
  `total_attempts` int NOT NULL DEFAULT '0',
  `total_errors` int NOT NULL DEFAULT '0',
  `error_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `unique_users` int NOT NULL DEFAULT '0',
  `avg_errors_per_user` decimal(5,2) DEFAULT NULL,
  `stat_date` date NOT NULL,
  `refreshed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_vses_courseware` (`courseware_code`),
  KEY `idx_vses_course` (`course_code`),
  KEY `idx_vses_dept` (`dept_code`),
  KEY `idx_vses_date` (`stat_date`)
) ENGINE=InnoDB AUTO_INCREMENT=128 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `wechat_binding` */

DROP TABLE IF EXISTS `wechat_binding`;

CREATE TABLE `wechat_binding` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台用户 ID',
  `openid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '微信小程序 openid',
  `unionid` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '微信 unionid（跨公众号/小程序唯一）',
  `nickname` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar_url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bound_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_wb_user` (`user_id`),
  UNIQUE KEY `uk_wb_openid` (`openid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Table structure for table `v_learner_overview` */

DROP TABLE IF EXISTS `v_learner_overview`;

/*!50001 DROP VIEW IF EXISTS `v_learner_overview` */;
/*!50001 DROP TABLE IF EXISTS `v_learner_overview` */;

/*!50001 CREATE TABLE  `v_learner_overview`(
 `user_id` varchar(50) ,
 `user_code` varchar(30) ,
 `user_name` varchar(100) ,
 `role_level` tinyint ,
 `dept_code` varchar(30) ,
 `dept_name` varchar(100) ,
 `class_code` varchar(30) ,
 `class_name` varchar(100) ,
 `position_code` varchar(30) ,
 `position_name` varchar(100) ,
 `gender` tinyint ,
 `education` varchar(30) ,
 `job_title` varchar(50) ,
 `last_login_at` datetime ,
 `org_code` varchar(30) 
)*/;

/*Table structure for table `v_course_overview` */

DROP TABLE IF EXISTS `v_course_overview`;

/*!50001 DROP VIEW IF EXISTS `v_course_overview` */;
/*!50001 DROP TABLE IF EXISTS `v_course_overview` */;

/*!50001 CREATE TABLE  `v_course_overview`(
 `course_code` varchar(30) ,
 `course_name` varchar(200) ,
 `credit` int ,
 `study_hours` int ,
 `category_code` varchar(30) ,
 `category_name` varchar(50) ,
 `dept_code` varchar(30) ,
 `dept_name` varchar(100) ,
 `is_published` tinyint(1) ,
 `courseware_count` bigint 
)*/;

/*View structure for view v_learner_overview */

/*!50001 DROP TABLE IF EXISTS `v_learner_overview` */;
/*!50001 DROP VIEW IF EXISTS `v_learner_overview` */;

/*!50001 CREATE ALGORITHM=UNDEFINED DEFINER=`webapp_user`@`%` SQL SECURITY DEFINER VIEW `v_learner_overview` AS select `u`.`user_id` AS `user_id`,`u`.`user_code` AS `user_code`,`u`.`user_name` AS `user_name`,`u`.`role_level` AS `role_level`,`u`.`dept_code` AS `dept_code`,`d`.`dept_name` AS `dept_name`,`sc`.`class_code` AS `class_code`,`cg`.`class_name` AS `class_name`,`u`.`position_code` AS `position_code`,`p`.`position_name` AS `position_name`,`up`.`gender` AS `gender`,`up`.`education` AS `education`,`up`.`job_title` AS `job_title`,`up`.`last_login_at` AS `last_login_at`,`d`.`org_code` AS `org_code` from (((((`user_info` `u` left join `department` `d` on((`u`.`dept_code` = `d`.`dept_code`))) left join `student_class` `sc` on((`u`.`user_id` = `sc`.`user_id`))) left join `class_group` `cg` on((`sc`.`class_code` = `cg`.`class_code`))) left join `position` `p` on((`u`.`position_code` = `p`.`position_code`))) left join `user_profile` `up` on((`u`.`user_id` = `up`.`user_id`))) where (`u`.`deleted_at` is null) */;

/*View structure for view v_course_overview */

/*!50001 DROP TABLE IF EXISTS `v_course_overview` */;
/*!50001 DROP VIEW IF EXISTS `v_course_overview` */;

/*!50001 CREATE ALGORITHM=UNDEFINED DEFINER=`webapp_user`@`%` SQL SECURITY DEFINER VIEW `v_course_overview` AS select `c`.`course_code` AS `course_code`,`c`.`course_name` AS `course_name`,`c`.`credit` AS `credit`,`c`.`study_hours` AS `study_hours`,`c`.`category_code` AS `category_code`,`cc`.`category_name` AS `category_name`,`c`.`dept_code` AS `dept_code`,`d`.`dept_name` AS `dept_name`,`c`.`is_published` AS `is_published`,(select count(0) from `course_courseware` `ccw` where (`ccw`.`course_code` = `c`.`course_code`)) AS `courseware_count` from ((`course` `c` left join `course_category` `cc` on((`c`.`category_code` = `cc`.`category_code`))) left join `department` `d` on((`c`.`dept_code` = `d`.`dept_code`))) where (`c`.`deleted_at` is null) */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
