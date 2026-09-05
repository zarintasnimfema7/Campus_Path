// Read the existing dashboard/evidence handoff; no separate fetching layer.
export function readSavedWorkflow(): Record<string, unknown> | null {
  const saved = sessionStorage.getItem("campuspath_workflow");
  if (!saved) return null;
  const value: unknown = JSON.parse(saved);
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Invalid saved analysis");
  }
  const workflow = value as Record<string, unknown>;
  for (const field of ["student", "job", "skill_gap", "plan"]) {
    if (workflow[field] != null && (typeof workflow[field] !== "object" || Array.isArray(workflow[field]))) {
      throw new Error("Invalid analysis section");
    }
  }
  const sections = workflow as Record<string, Record<string, unknown> | undefined>;
  for (const [section, fields] of Object.entries({
    student: ["skills", "certifications"],
    skill_gap: ["matched_skills", "partial_skills", "missing_skills"],
  })) {
    for (const field of fields) {
      const items = sections[section]?.[field];
      if (items != null && (!Array.isArray(items) || items.some(item => typeof item !== "string"))) {
        throw new Error("Invalid skill list");
      }
    }
  }
  for (const [section, fields] of Object.entries({ student: ["education", "experience"], plan: ["tasks"] })) {
    for (const field of fields) {
      const items = sections[section]?.[field];
      if (items != null && (!Array.isArray(items) || items.some(item => !item || typeof item !== "object" || Array.isArray(item)))) {
        throw new Error("Invalid analysis list");
      }
    }
  }
  return workflow;
}
