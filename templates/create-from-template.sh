#!/bin/bash

# Keboola Template Creator
# Quick script to create a new project from a template

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Keboola Development Template Creator${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to display available templates
show_templates() {
    echo -e "${GREEN}Available Templates:${NC}"
    echo ""
    echo -e "  ${YELLOW}1.${NC} custom-python    - Keboola Custom Python transformation"
    echo -e "  ${YELLOW}2.${NC} streamlit-app    - Interactive Streamlit data application"
    echo ""
}

# Function to copy template
copy_template() {
    local template=$1
    local destination=$2

    if [ ! -d "$SCRIPT_DIR/$template" ]; then
        echo -e "${RED}✗ Error: Template '$template' not found${NC}"
        exit 1
    fi

    if [ -d "$destination" ]; then
        echo -e "${RED}✗ Error: Directory '$destination' already exists${NC}"
        exit 1
    fi

    echo -e "${BLUE}Creating project from template...${NC}"

    # Copy template
    cp -r "$SCRIPT_DIR/$template" "$destination"

    # Remove .github workflows (user can add back if needed)
    if [ -d "$destination/.github" ]; then
        rm -rf "$destination/.github"
    fi

    # Remove .gitignore (user may have their own)
    if [ -f "$destination/.gitignore" ]; then
        rm "$destination/.gitignore"
    fi

    echo -e "${GREEN}✓ Template copied to: $destination${NC}"
}

# Main script
if [ $# -eq 0 ]; then
    # Interactive mode
    show_templates

    echo -e "${BLUE}Select a template:${NC}"
    read -p "Enter number (1-2) or name: " template_choice

    case "$template_choice" in
        1|custom-python)
            TEMPLATE="custom-python"
            ;;
        2|streamlit-app)
            TEMPLATE="streamlit-app"
            ;;
        *)
            echo -e "${RED}✗ Invalid choice${NC}"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${BLUE}Where should we create your project?${NC}"
    read -p "Enter directory name: " PROJECT_DIR

    if [ -z "$PROJECT_DIR" ]; then
        echo -e "${RED}✗ Directory name cannot be empty${NC}"
        exit 1
    fi

elif [ $# -eq 2 ]; then
    # Command line mode
    TEMPLATE=$1
    PROJECT_DIR=$2
else
    echo -e "${RED}✗ Usage: $0 [template] [directory]${NC}"
    echo ""
    show_templates
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 custom-python my-transformation"
    echo "  $0 streamlit-app my-data-app"
    echo "  $0  # Interactive mode"
    exit 1
fi

# Copy template
copy_template "$TEMPLATE" "$PROJECT_DIR"

# Show next steps
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Project created successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""

if [ "$TEMPLATE" == "custom-python" ]; then
    echo "  1. cd $PROJECT_DIR"
    echo "  2. Edit main.py and customize the process_data() function"
    echo "  3. Update requirements.txt if you need additional packages"
    echo "  4. Test locally with sample data"
    echo "  5. Deploy to Keboola Custom Python transformation"
    echo ""
    echo -e "${YELLOW}Documentation:${NC} $PROJECT_DIR/README.md"

elif [ "$TEMPLATE" == "streamlit-app" ]; then
    echo "  1. cd $PROJECT_DIR"
    echo "  2. uv pip install -r requirements.txt  # or: pip install -r requirements.txt"
    echo "  3. Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml"
    echo "  4. Add your Keboola Storage token to secrets.toml"
    echo "  5. Run: streamlit run app.py"
    echo ""
    echo -e "${YELLOW}Documentation:${NC} $PROJECT_DIR/README.md"
fi

echo ""
echo -e "${BLUE}Happy coding!${NC}"
echo ""
