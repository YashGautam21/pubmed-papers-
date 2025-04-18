# PubMed Papers Fetcher

A Python tool to fetch research papers from PubMed based on a user-specified query, filtering for papers with at least one author affiliated with a pharmaceutical or biotech company.

## Code Organization

The project is organized into two main components:

1. **`pubmed_papers` Module**: Core functionality for interacting with the PubMed API and processing papers.
   - `fetcher.py`: Handles API interactions and paper parsing via `get_papers()` function
   - `formatter.py`: Contains the `papers_to_csv()` function for data formatting
   - Data structures for representing papers and authors

2. **Command-line Interface**: A user-friendly CLI for accessing the module functionality.

## Installation

### Prerequisites

- Python 3.8.1+
- Git
- [Poetry](https://python-poetry.org/docs/#installation) (for dependency management)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/pubmed-papers.git
   cd pubmed-papers
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

This will set up all required dependencies and install the `get-papers-list` command.

## Usage

### Basic Usage

```bash
get-papers-list "cancer therapy"
```

Or if running from the project directory:

```bash
poetry run get-papers-list "cancer therapy"
```

This will search for papers about "cancer therapy" that have at least one author affiliated with a pharmaceutical or biotech company, and print the results to the console as CSV.

### Command-line Options

- `-h, --help`: Display usage instructions
- `-d, --debug`: Print debug information during execution
- `-f, --file FILENAME`: Specify a filename to save the results (if not provided, output to console)

### Examples

Search for papers about COVID-19 vaccines and save to a file:
```bash
get-papers-list "COVID-19 vaccine" -f covid_papers.csv
```

Search for papers with detailed query and debug information:
```bash
get-papers-list "alzheimer's disease AND (treatment OR therapy) AND 2020:2023[pdat]" -d
```

## Development

### Project Structure

```
pubmed-papers/
├── pubmed_papers/
│   ├── __init__.py
│   ├── fetcher.py
│   └── formatter.py
├── cli.py
├── pyproject.toml
├── README.md
└── ... (other project files)
```

### Tools Used

- **Poetry**: Dependency management and packaging
- **Requests**: HTTP library for API calls
- **Rich**: Enhanced terminal output
- **mypy**: Static type checking
- **pytest**: Testing framework
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting

## License

This project is licensed under the MIT License - see the LICENSE file for details.