import React from 'react';
import { Unit, Item } from '../../types/types';
import useSettings from '../../hooks/useSettings';

type Props = {
  units: Unit[];
  noUnitItems: Item[];
  availableItems: Item[];
  selectedNoUnitItems: number[];
  showAddUnitModal: () => void;
  editUnit: (id: number, name: string) => void;
  deleteUnit: (id: number, name: string) => void;
  moveUnitUp: (id: number) => void | Promise<void>;
  moveUnitDown: (id: number) => void | Promise<void>;
  selectAllNoUnitItems: () => void;
  clearNoUnitSelection: () => void;
  toggleNoUnitItemSelection: (id: number) => void;
  moveItemsToUnit: (id: number) => void | Promise<void>;
};

export default function UnitManager(props: Props) {
  const { formatPrice } = useSettings();
  const {
    units,
    noUnitItems,
    availableItems,
    selectedNoUnitItems,
    showAddUnitModal,
    editUnit,
    deleteUnit,
    moveUnitUp,
    moveUnitDown,
    selectAllNoUnitItems,
    clearNoUnitSelection,
    toggleNoUnitItemSelection,
    moveItemsToUnit,
  } = props;

  return (
    <div className="tab-content active">
      <div className="manage-units-content">
        <div className="categories-header">
          <h3>📏 Manage Units</h3>
          <button className="btn" onClick={showAddUnitModal}>
            ➕ Add Unit
          </button>
        </div>

        <div className="units-list">
          <h4>📋 Units</h4>
          <div className="units-container">
            {units.map((unit, index) => (
              <div key={unit.id} className="unit-card">
                <div className="unit-info">
                  <div className="unit-name">{unit.name}</div>
                  <div className="unit-stats">
                    Items: {availableItems.filter((item) => item.unit_id === unit.id).length}
                  </div>
                </div>
                <div className="unit-actions">
                  <div className="order-buttons">
                    <button
                      className="btn-order"
                      disabled={index === 0}
                      title="Move up"
                      onClick={() => moveUnitUp(unit.id)}
                    >
                      ⬆️
                    </button>
                    <button
                      className="btn-order"
                      disabled={index === units.length - 1}
                      title="Move down"
                      onClick={() => moveUnitDown(unit.id)}
                    >
                      ⬇️
                    </button>
                  </div>
                  <button className="btn-edit" onClick={() => editUnit(unit.id, unit.name)}>
                    ✏️ Edit
                  </button>
                  <button className="btn-delete" onClick={() => deleteUnit(unit.id, unit.name)}>
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
            {units.length === 0 && <div className="loading">No units</div>}
          </div>
        </div>

        {noUnitItems.length > 0 && (
          <div className="orphaned-items-section">
            <div className="orphaned-header">
              <h4>⚠️ Items without unit ({noUnitItems.length})</h4>
              <div className="selection-controls">
                <button
                  className="btn-small"
                  onClick={selectAllNoUnitItems}
                  disabled={selectedNoUnitItems.length === noUnitItems.length}
                >
                  Select all
                </button>
                <button
                  className="btn-small"
                  onClick={clearNoUnitSelection}
                  disabled={selectedNoUnitItems.length === 0}
                >
                  Clear selection
                </button>
                <span className="selection-info">
                  Selected: {selectedNoUnitItems.length} of {noUnitItems.length}
                </span>
              </div>
            </div>
            <div className="orphaned-items-container">
              {noUnitItems.map((item) => (
                <div
                  key={item.id}
                  className={`orphaned-item ${selectedNoUnitItems.includes(item.id) ? 'selected' : ''}`}
                  onClick={() => toggleNoUnitItemSelection(item.id)}
                >
                  <div className="item-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedNoUnitItems.includes(item.id)}
                      onChange={() => toggleNoUnitItemSelection(item.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                  <div className="item-info">
                    <div className="item-name">{item.name}</div>
                    <div className="item-price">
                      {formatPrice(item.price)} / {item.unit_name || 'no unit'}
                    </div>
                  </div>
                </div>
              ))}
              {selectedNoUnitItems.length > 0 && (
                <div className="orphaned-actions">
                  <p>Assign selected items to unit:</p>
                  <div className="category-selector">
                    <select
                      id="no-unit-select"
                      onChange={(e) => {
                        const unitId = parseInt(e.target.value);
                        if (unitId > 0) {
                          moveItemsToUnit(unitId);
                          (e.target as HTMLSelectElement).value = '';
                        }
                      }}
                    >
                      <option value="">Select a unit...</option>
                      {units.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
