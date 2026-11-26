#!/usr/bin/env node
import { greet } from "./greet.js";

const name = process.argv[2] ?? "világ";
console.log(greet(name));
