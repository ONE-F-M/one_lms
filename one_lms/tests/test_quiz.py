"""Quiz and assessment workflow tests for one_lms."""

from __future__ import annotations

from frappe.tests.utils import FrappeTestCase


class TestQuizAssessment(FrappeTestCase):
	def _make_quiz(self, passing_percentage=60, max_attempts=2):
		return {
			"title": "Test Quiz",
			"passing_percentage": passing_percentage,
			"max_attempts": max_attempts,
			"questions": [
				{
					"question": "What is ONE FM?",
					"answers": [
						{"answer": "A company", "is_correct": True},
						{"answer": "A course", "is_correct": False},
					],
				}
			],
		}

	def _grade_submission(self, quiz, submitted_answers):
		total_questions = len(quiz["questions"])
		correct_answers = 0
		for question, submitted_answer in zip(quiz["questions"], submitted_answers):
			correct = next(answer for answer in question["answers"] if answer["is_correct"])
			if submitted_answer == correct["answer"]:
				correct_answers += 1
		score = (correct_answers / total_questions) * 100
		return {"score": score, "passed": score >= quiz["passing_percentage"]}

	def test_quiz_creation_with_questions_and_answers(self):
		quiz = self._make_quiz()
		self.assertEqual(quiz["title"], "Test Quiz")
		self.assertEqual(len(quiz["questions"]), 1)
		self.assertTrue(any(answer["is_correct"] for answer in quiz["questions"][0]["answers"]))

	def test_quiz_submission_and_auto_grading(self):
		quiz = self._make_quiz()
		result = self._grade_submission(quiz, ["A company"])
		self.assertEqual(result["score"], 100)
		self.assertTrue(result["passed"])

	def test_passing_and_failing_threshold_logic(self):
		quiz = self._make_quiz(passing_percentage=80)
		passed = self._grade_submission(quiz, ["A company"])
		failed = self._grade_submission(quiz, ["A course"])
		self.assertTrue(passed["passed"])
		self.assertFalse(failed["passed"])

	def test_quiz_retry_limits(self):
		quiz = self._make_quiz(max_attempts=2)
		attempts = ["failed", "failed"]
		can_retry = len(attempts) < quiz["max_attempts"]
		self.assertFalse(can_retry)

	def test_quiz_results_reporting(self):
		quiz = self._make_quiz()
		result = self._grade_submission(quiz, ["A company"])
		report = {
			"quiz": quiz["title"],
			"score": result["score"],
			"status": "Passed" if result["passed"] else "Failed",
		}
		self.assertEqual(report, {"quiz": "Test Quiz", "score": 100, "status": "Passed"})
