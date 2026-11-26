import { test } from "node:test";
import assert from "node:assert/strict";
import { greet } from "./greet.js";

test("greet üdvözli a megadott nevet", () => {
  assert.equal(greet("Tibi"), "Szia, Tibi!");
});

test("greet levágja a felesleges szóközt", () => {
  assert.equal(greet("  Tibi "), "Szia, Tibi!");
});

test("greet üres névre hibát dob", () => {
  assert.throws(() => greet("   "), /nem lehet üres/);
});
test("greet több szavas nevet is kezel", () => {
  assert.equal(greet("Kiss Tibor"), "Szia, Kiss Tibor!");
});
