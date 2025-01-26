import { JsonSchema } from '@jsonforms/core';

export const sequenceSchema: JsonSchema = {
  type: 'object',
  properties: {
    metadata: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          title: 'Name',
          description: 'Sequence name'
        },
        version: {
          type: 'string',
          title: 'Version',
          description: 'Sequence version'
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
          description: 'Sequence author'
        },
        description: {
          type: 'string',
          title: 'Description',
          description: 'Sequence description'
        }
      },
      required: ['name', 'version', 'author']
    },
    steps: {
      type: 'array',
      title: 'Steps',
      items: {
        type: 'object',
        properties: {
          name: {
            type: 'string',
            title: 'Name',
            description: 'Step name'
          },
          step_type: {
            type: 'string',
            title: 'Type',
            enum: [
              'INITIALIZE',
              'TROUGH',
              'PATTERN',
              'PARAMETERS',
              'SPRAY',
              'SHUTDOWN'
            ],
            description: 'Step type'
          },
          description: {
            type: 'string',
            title: 'Description',
            description: 'Step description'
          },
          pattern_id: {
            type: 'string',
            title: 'Pattern ID',
            description: 'Associated pattern ID'
          },
          parameters: {
            type: 'string',
            title: 'Parameters',
            description: 'Associated parameters'
          },
          origin: {
            type: 'array',
            title: 'Origin',
            items: {
              type: 'number'
            },
            description: 'Origin coordinates'
          }
        },
        required: ['name', 'step_type']
      }
    }
  },
  required: ['metadata', 'steps']
};

export const sequenceUiSchema = {
  type: 'VerticalLayout',
  elements: [
    {
      type: 'Group',
      label: 'Metadata',
      elements: [
        {
          type: 'Control',
          scope: '#/properties/metadata/properties/name'
        },
        {
          type: 'Control',
          scope: '#/properties/metadata/properties/version'
        },
        {
          type: 'Control',
          scope: '#/properties/metadata/properties/author'
        },
        {
          type: 'Control',
          scope: '#/properties/metadata/properties/description',
          options: {
            multi: true
          }
        }
      ]
    },
    {
      type: 'Group',
      label: 'Steps',
      elements: [
        {
          type: 'Control',
          scope: '#/properties/steps',
          options: {
            detail: {
              type: 'VerticalLayout',
              elements: [
                {
                  type: 'Control',
                  scope: '#/properties/name'
                },
                {
                  type: 'Control',
                  scope: '#/properties/step_type'
                },
                {
                  type: 'Control',
                  scope: '#/properties/description',
                  options: {
                    multi: true
                  }
                },
                {
                  type: 'Control',
                  scope: '#/properties/pattern_id'
                },
                {
                  type: 'Control',
                  scope: '#/properties/parameters'
                },
                {
                  type: 'Control',
                  scope: '#/properties/origin'
                }
              ]
            }
          }
        }
      ]
    }
  ]
}; 