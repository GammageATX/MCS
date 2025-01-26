import { JsonSchema } from '@jsonforms/core';

export const powderSchema: JsonSchema = {
  type: 'object',
  properties: {
    name: {
      type: 'string',
      title: 'Name',
      description: 'Powder name'
    },
    type: {
      type: 'string',
      title: 'Type',
      description: 'Powder type'
    },
    size: {
      type: 'string',
      title: 'Size',
      description: 'Particle size range'
    },
    manufacturer: {
      type: 'string',
      title: 'Manufacturer',
      description: 'Powder manufacturer'
    },
    lot: {
      type: 'string',
      title: 'Lot Number',
      description: 'Manufacturing lot number'
    }
  },
  required: ['name', 'type', 'size', 'manufacturer', 'lot']
};

export const powderUiSchema = {
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
      scope: '#/properties/size'
    },
    {
      type: 'Control',
      scope: '#/properties/manufacturer'
    },
    {
      type: 'Control',
      scope: '#/properties/lot'
    }
  ]
}; 