import type {
  TriggerProviderApiEntity as GeneratedTriggerProvider,
  TriggerProviderSubscriptionApiEntity as GeneratedTriggerSubscription,
} from '@dify/contracts/api/console/workspaces/types.gen'
import { describe, expect, it } from 'vitest'
import {
  convertToTriggerWithProvider,
  normalizeTriggerProvider,
  normalizeTriggerSubscriptions,
} from '../use-triggers'

const createGeneratedTriggerProvider = (): GeneratedTriggerProvider => ({
  author: 'Dify',
  name: 'github',
  label: { en_US: 'GitHub' },
  description: { en_US: 'GitHub trigger provider' },
  tags: ['source-control'],
  events: [
    {
      name: 'issue_created',
      identity: {
        author: 'Dify',
        name: 'issue_created',
        label: { en_US: 'Issue created' },
        provider: 'github',
      },
      description: { en_US: 'Issue created event' },
      parameters: [
        {
          name: 'retry_count',
          label: { en_US: 'Retry count' },
          type: 'number',
          default: 0,
          required: false,
          multiple: false,
        },
      ],
      output_schema: {},
    },
  ],
})

describe('trigger provider normalization', () => {
  it('should preserve falsy event parameter defaults', () => {
    const normalizedProvider = normalizeTriggerProvider(createGeneratedTriggerProvider())
    const triggerWithProvider = convertToTriggerWithProvider(normalizedProvider)

    expect(normalizedProvider.events[0]?.parameters[0]?.default).toBe(0)
    expect(triggerWithProvider.events[0]?.parameters[0]?.default).toBe(0)
  })

  it('should return an empty subscription list when the API response is not an array', () => {
    const subscriptions = normalizeTriggerSubscriptions({ error: 'provider not found' })

    expect(subscriptions).toEqual([])
  })

  it('should normalize valid subscription API responses', () => {
    const subscriptions = normalizeTriggerSubscriptions([
      {
        id: 'subscription-1',
        name: 'GitHub issues',
        provider: 'github',
        credential_type: 'api-key',
        credentials: {},
        endpoint: 'https://example.com/webhook',
        parameters: {},
        properties: {},
        workflows_in_use: 2,
      } satisfies GeneratedTriggerSubscription,
    ])

    expect(subscriptions).toEqual([
      expect.objectContaining({
        id: 'subscription-1',
        workflows_in_use: 2,
      }),
    ])
  })
})
