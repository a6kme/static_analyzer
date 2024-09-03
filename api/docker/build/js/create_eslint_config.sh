#!/bin/bash

# Ensure a directory is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Set the directory to scan
DIRECTORY=$1

# Set the configuration file name
CONFIG_FILE="eslint.config.js"

# Initialize variables to track file types and dependencies
HAS_JS=false
HAS_TS=false
HAS_JSX=false
HAS_TSX=false
HAS_REACT=false
HAS_TYPESCRIPT=false

# Function to check for dependencies in package.json
check_dependency() {
  local package_json="$DIRECTORY/package.json"
  if [ -f "$package_json" ]; then
    if grep -q "\"$1\"" "$package_json"; then
      return 0
    else
      return 1
    fi
  else
    return 1
  fi
}

# Scan the provided directory for file extensions
for file in $(find "$DIRECTORY" -type f); do
  case "$file" in
    *.js)
      HAS_JS=true
      ;;
    *.jsx)
      HAS_JSX=true
      ;;
    *.ts)
      HAS_TS=true
      ;;
    *.tsx)
      HAS_TSX=true
      ;;
  esac
done

# Check for dependencies in package.json
if check_dependency "react"; then
  HAS_REACT=true
fi

if check_dependency "typescript"; then
  HAS_TYPESCRIPT=true
fi

# Generate ESLint configuration based on detected file types and dependencies
echo "Generating ESLint configuration in $CONFIG_FILE"

cat <<EOL > $CONFIG_FILE
// Auto-generated ESLint configuration

export default {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
EOL

# Add React configurations if necessary
if $HAS_JSX || $HAS_REACT; then
  echo "    'plugin:react/recommended'," >> $CONFIG_FILE
fi

# Add TypeScript configurations if necessary
if $HAS_TS || $HAS_TSX || $HAS_TYPESCRIPT; then
  echo "    'plugin:@typescript-eslint/recommended'," >> $CONFIG_FILE
fi

cat <<EOL >> $CONFIG_FILE
  ],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
EOL

# Add JSX support if necessary
if $HAS_JSX || $HAS_TSX; then
  echo "    ecmaFeatures: {" >> $CONFIG_FILE
  echo "      jsx: true," >> $CONFIG_FILE
  echo "    }," >> $CONFIG_FILE
fi

# Set TypeScript parser if necessary
if $HAS_TS || $HAS_TSX || $HAS_TYPESCRIPT; then
  echo "    parser: '@typescript-eslint/parser'," >> $CONFIG_FILE
fi

cat <<EOL >> $CONFIG_FILE
  },
  rules: {
    // Add custom rules here
  },
};

EOL

echo "ESLint configuration has been generated in $CONFIG_FILE"
