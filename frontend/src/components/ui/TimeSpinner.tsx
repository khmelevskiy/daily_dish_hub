import React from 'react';
import './TimeSpinner.css';

interface TimeSpinnerProps {
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
  placeholder?: string;
}

export default function TimeSpinner({ value, min, max, onChange, placeholder }: TimeSpinnerProps) {
  // Generate list of all possible values
  const values = Array.from({ length: max - min + 1 }, (_, i) => min + i);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newValue = parseInt(e.target.value);
    onChange(newValue);
  };

  return (
    <div className="time-select-container">
      <select className="time-select" value={value} onChange={handleChange} title={placeholder}>
        {values.map((val) => (
          <option key={val} value={val}>
            {val.toString().padStart(2, '0')}
          </option>
        ))}
      </select>
    </div>
  );
}
