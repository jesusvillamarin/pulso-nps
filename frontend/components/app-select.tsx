"use client";

import type { Key } from "@heroui/react";

import { Label, ListBox, Select } from "@heroui/react";

const EMPTY_SELECTION = "__pulso_all__";

interface AppSelectProps {
  label: string;
  value: string;
  options: readonly string[];
  onChange: (value: string) => void;
  emptyOptionLabel?: string;
  hideLabel?: boolean;
  className?: string;
}

export function AppSelect({
  label,
  value,
  options,
  onChange,
  emptyOptionLabel,
  hideLabel = false,
  className,
}: AppSelectProps) {
  const handleChange = (nextValue: Key | Key[] | null) => {
    const selected = Array.isArray(nextValue) ? nextValue[0] : nextValue;
    onChange(selected === EMPTY_SELECTION || selected == null ? "" : String(selected));
  };

  return (
    <Select
      fullWidth
      className={className}
      value={value || (emptyOptionLabel ? EMPTY_SELECTION : null)}
      variant="secondary"
      onChange={handleChange}
    >
      <Label className={hideLabel ? "sr-only" : undefined}>{label}</Label>
      <Select.Trigger className="pulso-select-trigger">
        <Select.Value />
        <Select.Indicator />
      </Select.Trigger>
      <Select.Popover className="pulso-select-popover">
        <ListBox>
          {emptyOptionLabel ? (
            <ListBox.Item id={EMPTY_SELECTION} textValue={emptyOptionLabel}>
              {emptyOptionLabel}
              <ListBox.ItemIndicator />
            </ListBox.Item>
          ) : null}
          {options.map((option) => (
            <ListBox.Item key={option} id={option} textValue={option}>
              {option}
              <ListBox.ItemIndicator />
            </ListBox.Item>
          ))}
        </ListBox>
      </Select.Popover>
    </Select>
  );
}
