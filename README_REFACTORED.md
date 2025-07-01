# CMS Data Processing Tool - Refactored Version

A professional, modular CMS (Centers for Medicare & Medicaid Services) data processing tool that extracts, transforms, and loads healthcare datasets into both CSV files and MySQL database.

## 🏗️ **Professional Architecture**

This refactored version follows professional software engineering principles with a clean, modular architecture:

```
3GHRCE/
├── src/                          # Source code package
│   ├── __init__.py
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py          # Centralized settings
│   ├── database/                 # Database operations
│   │   ├── __init__.py
│   │   └── mysql_manager.py     # MySQL connection & operations
│   ├── data_extraction/          # Data extraction layer
│   │   ├── __init__.py
│   │   └── cms_api_client.py    # CMS API interactions
│   ├── data_processing/          # Data processing layer
│   │   ├── __init__.py
│   │   └── dataset_processor.py # Dataset orchestration
│   └── utils/                    # Utilities
│       ├── __init__.py
│       └── logger.py            # Logging utilities
├── csv/                          # Output CSV files
├── main_refactored.py           # New modular main entry point
├── main.py                      # Original monolithic version
├── requirements.txt             # Dependencies
└── README_REFACTORED.md        # This file
```

## 🎯 **Key Improvements**

### 1. **Separation of Concerns**
- **Database Layer**: Isolated MySQL operations in `MySQLManager` class
- **API Layer**: Centralized CMS API interactions in `CMSAPIClient` class
- **Processing Layer**: Orchestration logic in `DatasetProcessor` class
- **Configuration**: Centralized settings management

### 2. **Object-Oriented Design**
- **Classes**: Each major component is a class with clear responsibilities
- **Inheritance**: Extensible design for future enhancements
- **Encapsulation**: Private methods and proper data hiding

### 3. **Professional Code Organization**
- **Modular Structure**: Logical separation of functionality
- **Clean Imports**: Clear dependency management
- **Type Hints**: Full type annotation for better IDE support
- **Documentation**: Comprehensive docstrings and comments

### 4. **Error Handling & Logging**
- **Centralized Logging**: Professional logging configuration
- **Exception Handling**: Proper error management throughout
- **Graceful Degradation**: Continues processing even if one dataset fails

## 🚀 **Usage**

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Run the refactored version
python main_refactored.py
```

### Configuration
All settings are centralized in `src/config/settings.py`:

```python
# Database settings
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Nithin@123',
    'database': 'cms_data'
}

# API settings
API_CONFIG = {
    'timeout': 30.0,
    'page_size': 5000,
    'max_pages': 10
}
```

## 📊 **Datasets Processed**

| # | Dataset Name | Type | Method |
|---|--------------|------|--------|
| 1 | SNF All Owners | API | UUID Extraction |
| 2 | SNF Enrollments | API | UUID Extraction |
| 3 | SNF Change of Ownership | API | UUID Extraction |
| 4 | SNF Entity Performance | API | UUID Extraction |
| 5 | SNF Cost Report | API | UUID Extraction |
| 6 | Provider Information | CSV | Direct Download |
| 7 | State Average Performance | CSV | Direct Download |

## 🔧 **Architecture Components**

### 1. **Database Manager** (`src/database/mysql_manager.py`)
```python
class MySQLManager:
    - get_connection()      # Establishes database connection
    - create_table()        # Creates tables from DataFrame schema
    - insert_data()         # Bulk inserts data
    - _sanitize_column_names() # Handles MySQL constraints
```

### 2. **API Client** (`src/data_extraction/cms_api_client.py`)
```python
class CMSAPIClient:
    - get_dataset_uuid()    # Extracts UUID using Playwright
    - fetch_all_data()      # Downloads all API data at once (no pagination)
    - download_csv_data()   # Downloads CSV files
    - get_csv_metadata()    # Fetches dataset metadata
```

### 3. **Dataset Processor** (`src/data_processing/dataset_processor.py`)
```python
class DatasetProcessor:
    - process_api_dataset()     # Handles API-based datasets
    - process_csv_dataset()     # Handles CSV datasets
    - process_state_average_dataset() # Special state data handler
```

### 4. **Settings** (`src/config/settings.py`)
```python
class Settings:
    - DB_CONFIG          # Database configuration
    - API_CONFIG         # API settings
    - API_DOCS_URLS      # Dataset URLs
    - CSV_DATASETS       # CSV dataset IDs
```

## 🛠️ **Development Benefits**

### **Maintainability**
- **Single Responsibility**: Each class has one clear purpose
- **Easy Testing**: Components can be tested in isolation
- **Clear Dependencies**: Explicit import structure

### **Extensibility**
- **New Datasets**: Easy to add new dataset types
- **New Storage**: Can add PostgreSQL, MongoDB, etc.
- **New APIs**: Can extend for other healthcare APIs

### **Professional Standards**
- **Type Safety**: Full type annotations
- **Error Handling**: Comprehensive exception management
- **Logging**: Professional logging throughout
- **Documentation**: Clear docstrings and comments

## 🔄 **Migration from Original**

The original `main.py` is preserved for reference. The new modular version:

1. **Same Functionality**: Processes identical datasets
2. **Better Organization**: Clean, professional structure
3. **Easier Maintenance**: Modular, testable components
4. **Future-Ready**: Extensible architecture

## 📈 **Performance & Reliability**

- **Async Processing**: Non-blocking I/O operations
- **Error Recovery**: Continues processing on individual failures
- **Resource Management**: Proper connection cleanup
- **Memory Efficiency**: Streaming data processing

## 🎉 **Getting Started**

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Setup MySQL**: Ensure MySQL server is running
4. **Install browsers**: `playwright install`
5. **Run**: `python main_refactored.py`

The tool will automatically:
- Create the `cms_data` database
- Download all 7 datasets
- Save CSV files to the `csv/` folder
- Store data in MySQL tables
- Provide detailed logging throughout

## 🤝 **Contributing**

This refactored version makes it easy to contribute:

1. **Clear Structure**: Know exactly where to add new features
2. **Isolated Components**: Test individual components
3. **Type Safety**: Catch errors early with type hints
4. **Documentation**: Clear code documentation

---

**Professional CMS Data Processing Tool** - Built with clean architecture principles! 🏥📊 