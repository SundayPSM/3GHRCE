# Table Name Mappings

This document shows the mapping between the original dataset names and the new, shorter table names used in the database.

## API Datasets

| Original Dataset Name | New Table Name | Description |
|----------------------|----------------|-------------|
| skilled_nursing_facility_all_owners | snf_owners | Skilled Nursing Facility All Owners |
| skilled_nursing_facility_enrollments | snf_enrollments | Skilled Nursing Facility Enrollments |
| skilled_nursing_facility_change_of_ownership | snf_ownership_changes | Skilled Nursing Facility Change of Ownership |
| nursing_home_affiliated_entity_performance_measures | nh_performance_measures | Nursing Home Affiliated Entity Performance Measures |

## CSV Datasets

| Original Dataset Name | New Table Name | Description |
|----------------------|----------------|-------------|
| provider | provider | Provider Data |
| state_average | state_average | State Average Performance Data |
| skilled_nursing_facility_cost_report | snf_cost_report | Skilled Nursing Facility Cost Report |

## Benefits of New Table Names

1. **Shorter**: Easier to type and reference in queries
2. **Consistent**: Follow a clear naming pattern
3. **Descriptive**: Still convey the meaning of the data
4. **Database-friendly**: Avoid potential issues with long table names

## Usage

The table name mappings are automatically applied in:
- `DatasetOrchestrator` - for API datasets
- `DatasetProcessor` - for CSV datasets
- `CMSAPIClient` - when inserting data directly

## Example

```python
# Old way
table_name = "skilled_nursing_facility_all_owners"

# New way  
table_name = "snf_owners"
```

## Database Schema

All tables follow the same structure:
- All columns are TEXT type for consistency
- Automatic `id` column with auto-increment
- `created_at` timestamp
- Data cleaning applied (NaN → empty string, whitespace trimming) 