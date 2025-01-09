import { Theme } from '@mui/material';
export interface JsonFormsTheme extends Theme {
    jsonforms?: {
        input?: {
            delete?: {
                background?: string;
            };
        };
    };
}
