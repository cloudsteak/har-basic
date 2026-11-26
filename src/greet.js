/**
 * Üdvözlő szöveget ad vissza.
 * @param {string} name
 * @returns {string}
 */
export function greet(name) {
  const trimmed = name.trim();
  if (!trimmed) {
    throw new Error("A név nem lehet üres");
  }
  return `Szia, ${trimmed}!`;
}
