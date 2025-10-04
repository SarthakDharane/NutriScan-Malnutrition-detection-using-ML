from __future__ import annotations

import os
from typing import Dict, Any, Optional


def _build_system_prompt() -> str:
	return (
		"You are a pediatric nutrition assistant. You explain BMI-for-age, WHO percentiles, z-scores, "
		"skin and nail health indicators, and provide general, non-diagnostic advice. Be concise, clear, "
		"supportive, and actionable. Encourage consulting healthcare professionals for severe findings."
	)


def _format_context(report: Dict[str, Any], patient: Dict[str, Any]) -> str:
	child_name = patient.get("child_name") or "the child"
	age_years = (patient.get("age_months") or 0) / 12.0
	bmi = patient.get("bmi") or 0.0
	skin_pred = report.get("skin_pred") or "unknown"
	nail_pred = report.get("nail_pred") or "unknown"
	risk_level = report.get("risk_level") or report.get("nutrition_status") or "Unknown"
	bmi_cat = report.get("bmi_category") or "Unknown"
	percentile = report.get("bmi_percentile")
	z = report.get("bmi_z_score")

	lines = [
		f"Child: {child_name}",
		f"Age (years): {age_years:.1f}",
		f"BMI: {bmi:.1f} ({bmi_cat})",
		f"WHO Percentile: {percentile:.1f}%" if percentile is not None else "WHO Percentile: n/a",
		f"Z-Score: {z:.2f}" if z is not None else "Z-Score: n/a",
		f"Skin: {skin_pred}",
		f"Nails: {nail_pred}",
		f"Risk Level: {risk_level}",
	]
	return "\n".join(lines)


def _openai_generate(prompt: str, temperature: float = 0.4) -> Optional[str]:
	try:
		from openai import OpenAI  # type: ignore
		api_key = os.environ.get("OPENAI_API_KEY")
		model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
		if not api_key:
			return None
		client = OpenAI(api_key=api_key)
		resp = client.chat.completions.create(
			model=model,
			messages=[
				{"role": "system", "content": _build_system_prompt()},
				{"role": "user", "content": prompt},
			],
			temperature=temperature,
		)
		return (resp.choices[0].message.content or "").strip()
	except Exception:
		return None


def _gemini_generate(prompt: str, temperature: float = 0.4) -> Optional[str]:
	try:
		import google.generativeai as genai  # type: ignore
		api_key = os.environ.get("GOOGLE_API_KEY")
		model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
		if not api_key:
			return None
		genai.configure(api_key=api_key)
		model = genai.GenerativeModel(model_name)
		resp = model.generate_content(
			[
				{"text": _build_system_prompt()},
				{"text": prompt},
			],
		)
		text = getattr(resp, "text", None) or (resp.candidates[0].content.parts[0].text if resp.candidates else "")
		return (text or "").strip()
	except Exception:
		return None


def generate_chat_response(user_message: str, report_data: Dict[str, Any] | None) -> str:
	"""Generate chatbot response using OpenAI or Gemini. Falls back to canned reply if unavailable."""
	context_text = ""
	if report_data:
		context_text = _format_context(report_data.get("report", {}), report_data.get("patient", {}))

	prompt = (
		"Context (if present):\n" + (context_text or "None") + "\n\n"
		"User question: " + (user_message or "") + "\n\n"
		"Answer with: (1) an explanation in simple language, (2) a brief takeaway, (3) 2-4 actionable, safe, non-diagnostic tips."
	)

	# Try OpenAI first, then Gemini
	text = _openai_generate(prompt)
	if not text:
		text = _gemini_generate(prompt)

	if text:
		return text

	# Safe fallback
	return (
		"I can explain the report and offer general tips. Please ensure you've set an API key for an LLM. "
		"Based on your inputs, focus on balanced meals, adequate hydration, regular sleep, and physical activity. "
		"If severe concerns appear (very low/high BMI, persistent symptoms), consult a healthcare professional."
	)
