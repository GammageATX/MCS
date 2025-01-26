import { JsonSchema } from '@jsonforms/core';

export const parameterSchema: JsonSchema = {
  type: 'object',
  properties: {
    name: {
      type: 'string',
      title: 'Name',
      description: 'Parameter name'
    },
    value: {
      type: 'number',
      title: 'Value',
      description: 'Parameter value'
    },
    created: {
      type: 'string',
      title: 'Created',
      format: 'date-time',
      description: 'Creation date'
    },
    author: {
      type: 'string',
      title: 'Author',
      description: 'Parameter author'
    },
    description: {
      type: 'string',
      title: 'Description',
      description: 'Parameter description'
    }
  },
  required: ['name', 'value']
};

export const parameterUiSchema = {
  type: 'VerticalLayout',
  elements: [
    {
      type: 'Control',
      scope: '#/properties/name'
    },
    {
      type: 'Control',
      scope: '#/properties/value'
    },
    {
      type: 'Control',
      scope: '#/properties/author'
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