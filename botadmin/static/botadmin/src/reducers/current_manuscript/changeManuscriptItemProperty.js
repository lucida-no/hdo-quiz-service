export default function changeManuscriptItemProperty(state, action) {
  const selectedItem = state.items.find(item => item.order === action.order);
  if (!selectedItem) {
    return state;
  }
  selectedItem[action.propertyName] = action.value;
  return {
    ...state,
    has_changes: true,
    items: [...state.items]
  };
}
