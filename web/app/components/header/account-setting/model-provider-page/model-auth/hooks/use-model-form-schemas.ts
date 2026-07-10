import type {
  Credential,
  CustomModelCredential,
  ModelProvider,
} from '../../declarations'
import { ModelTypeEnum } from '../../declarations'
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { FormTypeEnum } from '@/app/components/base/form/types'
import {
  genModelNameFormSchema,
  genModelTypeFormSchema,
} from '../../utils'

export const useModelFormSchemas = (
  provider: ModelProvider,
  providerFormSchemaPredefined: boolean,
  credentials?: Record<string, any>,
  credential?: Credential,
  model?: CustomModelCredential,
) => {
  const { t } = useTranslation()
  const {
    provider_credential_schema,
    supported_model_types,
    model_credential_schema,
  } = provider
  const formSchemas = useMemo(() => {
    const schemas = providerFormSchemaPredefined
      ? provider_credential_schema?.credential_form_schemas
      : model_credential_schema?.credential_form_schemas
    return Array.isArray(schemas) ? schemas : []
  }, [
    providerFormSchemaPredefined,
    provider_credential_schema?.credential_form_schemas,
    supported_model_types,
    model_credential_schema?.credential_form_schemas,
    model_credential_schema?.model,
    model,
  ])

  const formSchemasWithAuthorizationName = useMemo(() => {
    const authorizationNameSchema = {
      type: FormTypeEnum.textInput,
      variable: '__authorization_name__',
      label: t('auth.authorizationName', { ns: 'plugin' }),
      required: false,
    }

    return [
      authorizationNameSchema,
      ...formSchemas,
    ]
  }, [formSchemas, t])

  const modelTypeLabels = useMemo(() => {
    const buildLabel = (
      enKey:
        | 'modelProvider.modelTypeOption.llm'
        | 'modelProvider.modelTypeOption.textEmbedding'
        | 'modelProvider.modelTypeOption.rerank'
        | 'modelProvider.modelTypeOption.speechToText'
        | 'modelProvider.modelTypeOption.moderation'
        | 'modelProvider.modelTypeOption.tts',
    ) => ({
      en_US: t(enKey, { ns: 'common', lng: 'en-US' }),
      zh_Hans: t(enKey, { ns: 'common', lng: 'zh-Hans' }),
    })

    return {
      [ModelTypeEnum.textGeneration]: buildLabel('modelProvider.modelTypeOption.llm'),
      [ModelTypeEnum.textEmbedding]: buildLabel('modelProvider.modelTypeOption.textEmbedding'),
      [ModelTypeEnum.rerank]: buildLabel('modelProvider.modelTypeOption.rerank'),
      [ModelTypeEnum.speech2text]: buildLabel('modelProvider.modelTypeOption.speechToText'),
      [ModelTypeEnum.moderation]: buildLabel('modelProvider.modelTypeOption.moderation'),
      [ModelTypeEnum.tts]: buildLabel('modelProvider.modelTypeOption.tts'),
    }
  }, [t])

  const formValues = useMemo(() => {
    let result: any = {}
    formSchemas.forEach((schema) => {
      result[schema.variable] = schema.default
    })
    if (credential) {
      result = { ...result, __authorization_name__: credential?.credential_name }
      if (credentials)
        result = { ...result, ...credentials }
    }
    if (model)
      result = { ...result, __model_name: model?.model, __model_type: model?.model_type }
    return result
  }, [credentials, credential, model, formSchemas])

  const modelNameAndTypeFormSchemas = useMemo(() => {
    if (providerFormSchemaPredefined)
      return []

    const modelNameSchema = genModelNameFormSchema(model_credential_schema?.model)
    const modelTypeSchema = genModelTypeFormSchema(supported_model_types, modelTypeLabels)
    return [
      modelNameSchema,
      modelTypeSchema,
    ]
  }, [supported_model_types, model_credential_schema?.model, modelTypeLabels, providerFormSchemaPredefined])

  const modelNameAndTypeFormValues = useMemo(() => {
    let result = {}
    if (providerFormSchemaPredefined)
      return result

    if (model)
      result = { ...result, __model_name: model?.model, __model_type: model?.model_type }

    return result
  }, [model, providerFormSchemaPredefined])

  return {
    formSchemas: formSchemasWithAuthorizationName,
    formValues,
    modelNameAndTypeFormSchemas,
    modelNameAndTypeFormValues,
  }
}
