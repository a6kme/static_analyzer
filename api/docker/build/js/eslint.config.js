// Auto-generated ESLint flat configuration

import js from '@eslint/js';
import typescriptPlugin from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';

export default [
    js.configs.recommended,
    {
        files: ["*.ts", "*.tsx"],
        languageOptions: {
            parser: tsParser,
        },
        plugins: {
            '@typescript-eslint': typescriptPlugin,
        },
        rules: {
            ...typescriptPlugin.configs.recommended.rules,
            // Add or override TypeScript specific rules here
        },
    },
    {
        files: ["*.js", "*.jsx", "*.ts", "*.tsx"],
        languageOptions: {
            ecmaVersion: 2021,
            sourceType: 'module',
        },
        rules: {
            // Add custom rules here
        },
    },
];