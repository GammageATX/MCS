import { JsonSchema } from '@jsonforms/core';

export const nozzleSchema: JsonSchema = {
  type: 'object',
  properties: {
    name: {
      type: 'string',
      title: 'Name',
      description: 'Nozzle name'
    },
    manufacturer: {
      type: 'string',
      title: 'Manufacturer',
      description: 'Nozzle manufacturer'
    },
    type: {
      type: 'string',
      title: 'Type',
      enum: [
        'convergent-divergent',
        'convergent',
        'vented',
        'flat-plate',
        'de laval'
      ],
      description: 'Nozzle type'
    },
    description: {
      type: 'string',
      title: 'Description',
      description: 'Nozzle description'
    }
  },
  required: ['name', 'type', 'manufacturer']
};

export const nozzleUiSchema = {
  type: 'VerticalLayout',
  elements: [
    {
      type: 'Control',
      scope: '#/properties/name'
    },
    {
      type: 'Control',
      scope: '#/properties/manufacturer'
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