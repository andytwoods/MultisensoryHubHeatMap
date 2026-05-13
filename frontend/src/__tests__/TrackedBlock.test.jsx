import React from "react";
import { render, screen } from "@testing-library/react";
import TrackedBlock from "../TrackedBlock";

test("renders children", () => {
  render(<TrackedBlock blockId="test-block" topic="scent">Hello</TrackedBlock>);
  expect(screen.getByText("Hello")).toBeInTheDocument();
});

test("sets data-block-id attribute", () => {
  const { container } = render(<TrackedBlock blockId="scent-intro" topic="scent">Content</TrackedBlock>);
  expect(container.firstChild.getAttribute("data-block-id")).toBe("scent-intro");
});

test("warns in dev if blockId missing", () => {
  const warn = jest.spyOn(console, "warn").mockImplementation(() => {});
  // Mock process.env.NODE_ENV
  const oldEnv = process.env.NODE_ENV;
  process.env.NODE_ENV = 'development';
  
  render(<TrackedBlock topic="scent">Content</TrackedBlock>);
  expect(warn).toHaveBeenCalled();
  
  process.env.NODE_ENV = oldEnv;
  warn.mockRestore();
});
