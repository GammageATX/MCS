import { JsonSchema } from '@jsonforms/core';

export const patternSchema: JsonSchema = {
  type: 'object',
  properties: {
    name: {
      type: 'string',
      title: 'Name',
      description: 'Pattern name'
    },
    type: {
      type: 'string',
      title: 'Type',
      enum: ['linear', 'serpentine', 'spiral'],
      description: 'Pattern type'
    },
    description: {
      type: 'string',
      title: 'Description',
      description: 'Pattern description'
    }
  },
  required: ['name', 'type']
};

export const patternUiSchema = {
  type: 'VerticalLayout',
  elements: [
    {
      type: 'Control',
      scope: '#/properties/name'
    },
    {
      type: 'Control',
      scope: '#/properties/type'
    },
    {
      type: 'Control',
      scope: '#/properties/description',
      options: {
        multi: true
      }
    }
  ]
}; 