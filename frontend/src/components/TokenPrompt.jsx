import { useState } from "react";

export default function TokenPrompt({ onSubmit }) {
  const [value, setValue] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (value.trim()) onSubmit(value.trim());
  }

  return (
    <form className="add-form" onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
      <input
        type="password"
        placeholder="Dashboard token"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        autoFocus
      />
      <button type="submit" disabled={!value.trim()}>Unlock</button>
    </form>
  );
}
