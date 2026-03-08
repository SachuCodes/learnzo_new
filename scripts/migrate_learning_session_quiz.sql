-- Migration: add topic quiz fields to learning_sessions (for quiz score and bandit-based mode switching).
-- Run once: mysql -u learnzo_user -p learnzo < scripts/migrate_learning_session_quiz.sql
-- If columns already exist, the ALTER will error; that is expected.

USE learnzo;

ALTER TABLE learning_sessions
  ADD COLUMN quiz_score FLOAT NULL,
  ADD COLUMN quiz_correct_answers JSON NULL,
  ADD COLUMN quiz_questions_snapshot JSON NULL;
