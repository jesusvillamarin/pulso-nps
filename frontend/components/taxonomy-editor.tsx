"use client";

import { Button, Input } from "@heroui/react";
import { Plus, Trash2 } from "lucide-react";
import type { AreaConfig } from "@/lib/types";

export function TaxonomyEditor({ value, onChange }: { value: AreaConfig[]; onChange: (value: AreaConfig[]) => void }) {
  const updateArea = (index: number, patch: Partial<AreaConfig>) => {
    onChange(value.map((area, current) => current === index ? { ...area, ...patch } : area));
  };

  return (
    <div>
      {value.map((area, index) => (
        <div className="taxonomy-area" key={`${index}-${area.name}`}>
          <div className="taxonomy-grid">
            <Input
              aria-label={`Nombre del área ${index + 1}`}
              value={area.name}
              variant="secondary"
              onChange={(event) => updateArea(index, { name: event.target.value })}
            />
            <Input
              aria-label={`Categorías del área ${area.name}`}
              value={area.categories.map((category) => category.name).join(", ")}
              variant="secondary"
              onChange={(event) => updateArea(index, {
                categories: event.target.value.split(",").map((name) => name.trim()).filter(Boolean).map((name) => ({ name, description: name })),
              })}
            />
          </div>
          <div className="taxonomy-categories">Separa las categorías con comas.</div>
          {value.length > 1 ? (
            <Button size="sm" variant="ghost" onPress={() => onChange(value.filter((_, current) => current !== index))}>
              <Trash2 size={14} /> Eliminar área
            </Button>
          ) : null}
        </div>
      ))}
      <Button size="sm" variant="secondary" onPress={() => onChange([...value, { name: "Nueva área", description: "", categories: [{ name: "General", description: "" }] }])}>
        <Plus size={14} /> Añadir área
      </Button>
    </div>
  );
}
