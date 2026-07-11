import type { FC } from 'react'
import type {
  Credential,
  CustomConfigurationModelFixedFields,
  CustomModel,
  DiscoveredModel,
  ModelProvider,
} from '../declarations'
import type {
  FormRefObject,
  FormSchema,
} from '@/app/components/base/form/types'
import {
  AlertDialog,
  AlertDialogActions,
  AlertDialogCancelButton,
  AlertDialogConfirmButton,
  AlertDialogContent,
  AlertDialogTitle,
} from '@langgenius/dify-ui/alert-dialog'
import { Button } from '@langgenius/dify-ui/button'
import { Checkbox } from '@langgenius/dify-ui/checkbox'
import {
  Dialog,
  DialogCloseButton,
  DialogContent,
} from '@langgenius/dify-ui/dialog'
import { toast } from '@langgenius/dify-ui/toast'
import {
  memo,
  useCallback,
  useMemo,
  useRef,
  useState,
} from 'react'
import { useTranslation } from 'react-i18next'
import Badge from '@/app/components/base/badge'
import AuthForm from '@/app/components/base/form/form-scenarios/auth'
import { LinkExternal02 } from '@/app/components/base/icons/src/vender/line/general'
import { Lock01 } from '@/app/components/base/icons/src/vender/solid/security'
import Loading from '@/app/components/base/loading'
import {
  useAuth,
  useCredentialData,
} from '@/app/components/header/account-setting/model-provider-page/model-auth/hooks'
import ModelIcon from '@/app/components/header/account-setting/model-provider-page/model-icon'
import { useCredentialPermissions } from '@/hooks/use-credential-permissions'
import { useRenderI18nObject } from '@/hooks/use-i18n'
import { useDiscoverProviderModels } from '@/service/use-models'
import {
  ConfigurationMethodEnum,
  FormTypeEnum,
  ModelModalModeEnum,
} from '../declarations'
import {
  useLanguage,
} from '../hooks'
import { CredentialSelector } from '../model-auth'
import { useModelFormSchemas } from '../model-auth/hooks'

type ModelModalProps = {
  provider: ModelProvider
  configurateMethod: ConfigurationMethodEnum
  currentCustomConfigurationModelFixedFields?: CustomConfigurationModelFixedFields
  onCancel: () => void
  onSave: (formValues?: Record<string, any>) => void
  onRemove: (formValues?: Record<string, any>) => void
  model?: CustomModel
  credential?: Credential
  isModelCredential?: boolean
  mode?: ModelModalModeEnum
}

const ModelModal: FC<ModelModalProps> = ({
  provider,
  configurateMethod,
  currentCustomConfigurationModelFixedFields,
  onCancel,
  onSave,
  model,
  credential,
  isModelCredential,
  mode = ModelModalModeEnum.configProviderCredential,
}) => {
  const renderI18nObject = useRenderI18nObject()
  const providerFormSchemaPredefined = configurateMethod === ConfigurationMethodEnum.predefinedModel
  const {
    isLoading,
    credentialData,
  } = useCredentialData(provider, providerFormSchemaPredefined, isModelCredential, credential, model)
  const {
    handleSaveCredential,
    handleSaveModelCredentials,
    handleConfirmDelete,
    deleteCredentialId,
    closeConfirmDelete,
    openConfirmDelete,
    doingAction,
    handleActiveCredential,
  } = useAuth(
    provider,
    configurateMethod,
    currentCustomConfigurationModelFixedFields,
    {
      isModelCredential,
      mode,
    },
  )
  const {
    credentials: formSchemasValue,
    available_credentials,
  } = credentialData as any

  const { canUseCredential, canCreateCredential, canManageCredential } = useCredentialPermissions()
  const { t } = useTranslation()
  const language = useLanguage()
  const {
    formSchemas,
    formValues,
    modelNameAndTypeFormSchemas,
    modelNameAndTypeFormValues,
  } = useModelFormSchemas(provider, providerFormSchemaPredefined, formSchemasValue, credential, model)
  const formRef1 = useRef<FormRefObject>(null)
  const [selectedCredential, setSelectedCredential] = useState<Credential & { addNewCredential?: boolean } | undefined>()
  const formRef2 = useRef<FormRefObject>(null)
  const [discoveredModels, setDiscoveredModels] = useState<DiscoveredModel[]>([])
  const [selectedDiscoveredModelKeys, setSelectedDiscoveredModelKeys] = useState<string[]>([])
  const [discoverError, setDiscoverError] = useState('')
  const { mutateAsync: discoverProviderModels, isPending: isDiscoveringModels } = useDiscoverProviderModels(provider.provider)
  const reusableModelCredential = useMemo(() => {
    for (const customModel of provider.custom_configuration.custom_models || []) {
      const credentialId = customModel.current_credential_id
        || customModel.available_model_credentials?.find(item => !item.not_allowed_to_use)?.credential_id
      if (credentialId) {
        return {
          credentialId,
          credentialName: customModel.current_credential_name,
          model: customModel.model,
          modelType: customModel.model_type,
        }
      }
    }
    return undefined
  }, [provider.custom_configuration.custom_models])
  const isEditMode = !!credential && !!Object.keys(formSchemasValue || {}).filter((key) => {
    return key !== '__model_name' && key !== '__model_type' && !!formValues[key]
  }).length && canManageCredential

  const supportsModelDiscovery = useMemo(() => {
    const variables = new Set((provider.model_credential_schema?.credential_form_schemas || []).map(schema => schema.variable))
    const hasBaseUrl = variables.has('proxy_base_url') || variables.has('endpoint_url')
    const hasApiKey = variables.has('proxy_api_key') || variables.has('api_key') || variables.has('openai_api_key')
    return mode === ModelModalModeEnum.configCustomModel && !credential && hasBaseUrl && hasApiKey
  }, [credential, mode, provider.model_credential_schema])

  const getDiscoveredModelKey = useCallback((discoveredModel: DiscoveredModel) => {
    return `${discoveredModel.model_type}:${discoveredModel.model}`
  }, [])

  const selectedDiscoveredModels = useMemo(() => {
    const selectedKeys = new Set(selectedDiscoveredModelKeys)
    return discoveredModels.filter(discoveredModel => selectedKeys.has(getDiscoveredModelKey(discoveredModel)))
  }, [discoveredModels, getDiscoveredModelKey, selectedDiscoveredModelKeys])

  const handleSave = useCallback(async () => {
    if (mode === ModelModalModeEnum.addCustomModelToModelList && selectedCredential && !selectedCredential?.addNewCredential) {
      if (!canUseCredential)
        return

      handleActiveCredential(selectedCredential, model)
      onCancel()
      return
    }

    const canSubmitCredentialForm = credential ? canManageCredential : canCreateCredential
    if (!canSubmitCredentialForm)
      return

    let modelNameAndTypeIsCheckValidated = true
    let modelNameAndTypeValues: Record<string, any> = {}
    const firstSelectedDiscoveredModel = selectedDiscoveredModels.at(0)

    if (mode === ModelModalModeEnum.configCustomModel && firstSelectedDiscoveredModel) {
      modelNameAndTypeValues = {
        __model_name: firstSelectedDiscoveredModel.model,
        __model_type: firstSelectedDiscoveredModel.model_type,
      }
    }
    else if (mode === ModelModalModeEnum.configCustomModel) {
      const formResult = formRef1.current?.getFormValues({
        needCheckValidatedValues: true,
      }) || { isCheckValidated: false, values: {} }
      modelNameAndTypeIsCheckValidated = formResult.isCheckValidated
      modelNameAndTypeValues = formResult.values
    }

    if (
      mode === ModelModalModeEnum.configModelCredential
      || (mode === ModelModalModeEnum.addCustomModelToModelList && selectedCredential?.addNewCredential)
    ) {
      const modelContext = model ?? (currentCustomConfigurationModelFixedFields
        ? {
            model: currentCustomConfigurationModelFixedFields.__model_name,
            model_type: currentCustomConfigurationModelFixedFields.__model_type,
          }
        : undefined)
      if (!modelContext)
        return

      modelNameAndTypeValues = {
        __model_name: modelContext.model,
        __model_type: modelContext.model_type,
      }
    }
    const credentialFormResult = reusableModelCredential
      ? { isCheckValidated: true, values: {} }
      : formRef2.current?.getFormValues({
          needCheckValidatedValues: true,
          needTransformWhenSecretFieldIsPristine: true,
        }) || { isCheckValidated: false, values: {} }
    const { isCheckValidated, values } = credentialFormResult
    if (!isCheckValidated || !modelNameAndTypeIsCheckValidated)
      return

    const {
      __model_name,
      __model_type,
    } = modelNameAndTypeValues
    const {
      __authorization_name__,
      ...rest
    } = values
    const shouldSaveModelCredential = mode === ModelModalModeEnum.configCustomModel
      || mode === ModelModalModeEnum.configModelCredential
      || (mode === ModelModalModeEnum.addCustomModelToModelList && selectedCredential?.addNewCredential)
    if (shouldSaveModelCredential) {
      if (!__model_name || !__model_type)
        return

      if (selectedDiscoveredModels.length) {
        await handleSaveModelCredentials({
          credentials: rest,
          name: __authorization_name__ || reusableModelCredential?.credentialName,
          models: selectedDiscoveredModels.map(discoveredModel => ({
            model: discoveredModel.model,
            model_type: discoveredModel.model_type,
          })),
          source_model: reusableModelCredential?.model,
          source_model_type: reusableModelCredential?.modelType,
          source_credential_id: reusableModelCredential?.credentialId,
        })
      }
      else {
        await handleSaveCredential({
          credential_id: credential?.credential_id,
          credentials: rest,
          name: __authorization_name__,
          model: __model_name,
          model_type: __model_type,
        })
      }
    }
    else {
      await handleSaveCredential({
        credential_id: credential?.credential_id,
        credentials: rest,
        name: __authorization_name__,
      })
    }
    onSave(values)
  }, [mode, selectedCredential, model, currentCustomConfigurationModelFixedFields, canUseCredential, canCreateCredential, canManageCredential, onSave, handleActiveCredential, onCancel, handleSaveCredential, handleSaveModelCredentials, credential, selectedDiscoveredModels, reusableModelCredential])

  const modalTitle = useMemo(() => {
    let label = t('modelProvider.auth.apiKeyModal.title', { ns: 'common' })

    if (mode === ModelModalModeEnum.configCustomModel || mode === ModelModalModeEnum.addCustomModelToModelList)
      label = t('modelProvider.auth.addModel', { ns: 'common' })
    if (mode === ModelModalModeEnum.configModelCredential) {
      if (credential)
        label = t('modelProvider.auth.editModelCredential', { ns: 'common' })
      else
        label = t('modelProvider.auth.addModelCredential', { ns: 'common' })
    }

    return (
      <div className="title-2xl-semi-bold text-text-primary">
        {label}
      </div>
    )
  }, [t, mode, credential])

  const modalDesc = useMemo(() => {
    if (providerFormSchemaPredefined) {
      return (
        <div className="mt-1 system-xs-regular text-text-tertiary">
          {t('modelProvider.auth.apiKeyModal.desc', { ns: 'common' })}
        </div>
      )
    }

    return null
  }, [providerFormSchemaPredefined, t])

  const modalModel = useMemo(() => {
    if (mode === ModelModalModeEnum.configCustomModel) {
      return (
        <div className="mt-2 flex items-center">
          <ModelIcon
            className="mr-2 size-4 shrink-0"
            provider={provider}
          />
          <div className="mr-1 system-md-regular text-text-secondary">{renderI18nObject(provider.label)}</div>
        </div>
      )
    }
    if (model && (mode === ModelModalModeEnum.configModelCredential || mode === ModelModalModeEnum.addCustomModelToModelList)) {
      return (
        <div className="mt-2 flex items-center">
          <ModelIcon
            className="mr-2 size-4 shrink-0"
            provider={provider}
            modelName={model.model}
          />
          <div className="mr-1 system-md-regular text-text-secondary">{model.model}</div>
          <Badge>{model.model_type}</Badge>
        </div>
      )
    }

    return null
  }, [model, provider, mode, renderI18nObject])

  const showCredentialLabel = useMemo(() => {
    if (mode === ModelModalModeEnum.configCustomModel)
      return !reusableModelCredential
    if (mode === ModelModalModeEnum.addCustomModelToModelList)
      return selectedCredential?.addNewCredential
  }, [mode, reusableModelCredential, selectedCredential])
  const showCredentialForm = useMemo(() => {
    if (mode === ModelModalModeEnum.configCustomModel && reusableModelCredential)
      return false
    if (mode !== ModelModalModeEnum.addCustomModelToModelList)
      return true
    return selectedCredential?.addNewCredential
  }, [mode, reusableModelCredential, selectedCredential])
  const saveButtonText = useMemo(() => {
    if (mode === ModelModalModeEnum.addCustomModelToModelList || mode === ModelModalModeEnum.configCustomModel)
      return t('operation.add', { ns: 'common' })
    return t('operation.save', { ns: 'common' })
  }, [mode, t])
  const canSaveCredentialChange = mode === ModelModalModeEnum.addCustomModelToModelList && selectedCredential && !selectedCredential.addNewCredential
    ? canUseCredential
    : credential ? canManageCredential : canCreateCredential

  const handleDeleteCredential = useCallback(() => {
    handleConfirmDelete()
    onCancel()
  }, [handleConfirmDelete, onCancel])

  const handleDiscoverModels = useCallback(async () => {
    const credentialFormResult = reusableModelCredential
      ? { isCheckValidated: true, values: {} }
      : formRef2.current?.getFormValues({
          needCheckValidatedValues: true,
          needTransformWhenSecretFieldIsPristine: true,
        }) || { isCheckValidated: false, values: {} }

    if (!credentialFormResult.isCheckValidated)
      return

    const modelForm = formRef1.current?.getForm()
    const modelType = modelForm?.state?.values?.__model_type || provider.supported_model_types[0]
    if (!modelType)
      return

    const { __authorization_name__, ...credentials } = credentialFormResult.values

    try {
      setDiscoverError('')
      setDiscoveredModels([])
      setSelectedDiscoveredModelKeys([])
      const response = await discoverProviderModels({
        model_type: modelType,
        credentials,
        source_model: reusableModelCredential?.model,
        source_model_type: reusableModelCredential?.modelType,
        source_credential_id: reusableModelCredential?.credentialId,
      })
      const existingModelKeys = new Set((provider.custom_configuration.custom_models || []).map(existingModel => (
        `${existingModel.model_type}:${existingModel.model}`
      )))
      const models = (response.data || []).filter(discoveredModel => (
        !existingModelKeys.has(getDiscoveredModelKey(discoveredModel))
      ))
      setDiscoveredModels(models)
      if (!models.length) {
        const message = t('modelProvider.auth.fetchModelsEmpty', { ns: 'common' })
        setDiscoverError(message)
        toast.error(message)
      }
    }
    catch (error: any) {
      const message = error?.message || t('api.actionFailed', { ns: 'common' })
      setDiscoveredModels([])
      setSelectedDiscoveredModelKeys([])
      setDiscoverError(message)
      toast.error(message)
    }
  }, [discoverProviderModels, getDiscoveredModelKey, provider.custom_configuration.custom_models, provider.supported_model_types, reusableModelCredential, t])

  const handleToggleDiscoveredModel = useCallback((selectedModel: DiscoveredModel) => {
    const selectedKey = getDiscoveredModelKey(selectedModel)
    setSelectedDiscoveredModelKeys((currentKeys) => {
      if (currentKeys.includes(selectedKey))
        return currentKeys.filter(key => key !== selectedKey)
      return [...currentKeys, selectedKey]
    })
  }, [getDiscoveredModelKey])

  const handleToggleAllDiscoveredModels = useCallback(() => {
    if (selectedDiscoveredModelKeys.length === discoveredModels.length) {
      setSelectedDiscoveredModelKeys([])
      return
    }
    setSelectedDiscoveredModelKeys(discoveredModels.map(getDiscoveredModelKey))
  }, [discoveredModels, getDiscoveredModelKey, selectedDiscoveredModelKeys.length])

  const handleModelNameAndTypeChange = useCallback((field: string, value: any) => {
    const {
      getForm,
    } = formRef2.current as FormRefObject || {}
    if (getForm())
      getForm()?.setFieldValue(field, value)
  }, [])
  const notAllowCustomCredential = provider.allow_custom_token === false

  const handleOpenChange = useCallback((open: boolean) => {
    if (!open)
      onCancel()
  }, [onCancel])

  const handleConfirmOpenChange = useCallback((open: boolean) => {
    if (!open)
      closeConfirmDelete()
  }, [closeConfirmDelete])

  return (
    <Dialog open onOpenChange={handleOpenChange}>
      <DialogContent
        backdropProps={{ forceRender: true }}
        className="flex w-[640px] max-w-[640px] flex-col overflow-hidden p-0"
      >
        <DialogCloseButton className="top-5 right-5 size-8" />
        <div className="shrink-0 p-6 pb-3">
          {modalTitle}
          {modalDesc}
          {modalModel}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-3">
          {
            mode === ModelModalModeEnum.configCustomModel && (
              <>
                <AuthForm
                  formSchemas={modelNameAndTypeFormSchemas.map((formSchema) => {
                    return {
                      ...formSchema,
                      name: formSchema.variable,
                    }
                  }) as FormSchema[]}
                  defaultValues={modelNameAndTypeFormValues}
                  inputClassName="justify-start"
                  ref={formRef1}
                  onChange={handleModelNameAndTypeChange}
                />
                {
                  reusableModelCredential && (
                    <div className="mt-3 rounded-lg border border-divider-subtle bg-background-default-subtle px-3 py-2 system-xs-regular text-text-secondary">
                      {t('modelProvider.auth.modelCredential', { ns: 'common' })}
                      {`: ${reusableModelCredential.model}`}
                      {reusableModelCredential.credentialName ? ` · ${reusableModelCredential.credentialName}` : ''}
                    </div>
                  )
                }
                {
                  supportsModelDiscovery && (
                    <div className="mt-3 rounded-xl border border-divider-subtle bg-background-default-subtle p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="system-xs-regular text-text-tertiary">
                          {t('modelProvider.auth.fetchModelsTip', { ns: 'common' })}
                        </div>
                        <Button
                          size="small"
                          onClick={handleDiscoverModels}
                          loading={isDiscoveringModels}
                        >
                          {t('modelProvider.auth.fetchModels', { ns: 'common' })}
                        </Button>
                      </div>
                      {
                        !!discoverError && (
                          <div className="mt-2 system-xs-regular text-text-destructive">{discoverError}</div>
                        )
                      }
                      {
                        !!discoveredModels.length && (
                          <div className="mt-3">
                            <div className="mb-2 flex items-center justify-between">
                              <Button size="small" onClick={handleToggleAllDiscoveredModels}>
                                {t('operation.selectAll', { ns: 'common' })}
                              </Button>
                              <span className="system-xs-regular text-text-tertiary">
                                {t('dynamicSelect.selected', { ns: 'common', count: selectedDiscoveredModels.length })}
                              </span>
                            </div>
                            <div className="max-h-48 space-y-1 overflow-y-auto">
                              {discoveredModels.map(discoveredModel => (
                                <div
                                  key={`${discoveredModel.model_type}-${discoveredModel.model}`}
                                  role="checkbox"
                                  aria-checked={selectedDiscoveredModelKeys.includes(getDiscoveredModelKey(discoveredModel))}
                                  tabIndex={0}
                                  className="flex w-full cursor-pointer items-center gap-3 rounded-lg border border-divider-subtle px-3 py-2 text-left hover:bg-state-base-hover"
                                  onClick={() => handleToggleDiscoveredModel(discoveredModel)}
                                  onKeyDown={(event) => {
                                    if (event.key === ' ' || event.key === 'Enter') {
                                      event.preventDefault()
                                      handleToggleDiscoveredModel(discoveredModel)
                                    }
                                  }}
                                >
                                  <Checkbox
                                    checked={selectedDiscoveredModelKeys.includes(getDiscoveredModelKey(discoveredModel))}
                                    className="pointer-events-none"
                                  />
                                  <div className="min-w-0 flex-1">
                                    <div className="truncate system-sm-medium text-text-primary">
                                      {discoveredModel.label || discoveredModel.model}
                                    </div>
                                    <div className="truncate system-xs-regular text-text-tertiary">
                                      {discoveredModel.model}
                                    </div>
                                  </div>
                                  <Badge>{discoveredModel.model_type}</Badge>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      }
                    </div>
                  )
                }
              </>
            )
          }
          {
            mode === ModelModalModeEnum.addCustomModelToModelList && (
              <CredentialSelector
                credentials={available_credentials || []}
                onSelect={setSelectedCredential}
                selectedCredential={selectedCredential}
                disabled={isLoading}
                notAllowAddNewCredential={notAllowCustomCredential || !canCreateCredential}
              />
            )
          }
          {
            showCredentialLabel && (
              <div className="mt-6 mb-3 flex items-center system-xs-medium-uppercase text-text-tertiary">
                {t('modelProvider.auth.modelCredential', { ns: 'common' })}
                <div className="ml-2 h-px grow bg-linear-to-r from-divider-regular to-background-gradient-mask-transparent" />
              </div>
            )
          }
          {
            isLoading && (
              <div className="mt-3 flex items-center justify-center">
                <Loading />
              </div>
            )
          }
          {
            !isLoading
            && showCredentialForm
            && (
              <AuthForm
                formSchemas={formSchemas.map((formSchema) => {
                  return {
                    ...formSchema,
                    name: formSchema.variable,
                    showRadioUI: formSchema.type === FormTypeEnum.radio,
                  }
                }) as FormSchema[]}
                defaultValues={formValues}
                inputClassName="justify-start"
                ref={formRef2}
              />
            )
          }
        </div>
        <div className="flex shrink-0 justify-between p-6 pt-5">
          {
            (provider.help && (provider.help.title || provider.help.url))
              ? (
                  <a
                    href={provider.help?.url[language] || provider.help?.url.en_US}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 inline-block align-middle system-xs-regular text-text-accent"
                    onClick={e => !provider.help.url && e.preventDefault()}
                  >
                    {provider.help.title?.[language] || provider.help.url[language] || provider.help.title?.en_US || provider.help.url.en_US}
                    <LinkExternal02 className="mt-[-2px] ml-1 inline-block h-3 w-3" />
                  </a>
                )
              : <div />
          }
          <div className="ml-2 flex items-center justify-end space-x-2">
            {
              isEditMode && (
                <Button
                  variant="primary"
                  tone="destructive"
                  onClick={() => openConfirmDelete(credential, model)}
                >
                  {t('operation.remove', { ns: 'common' })}
                </Button>
              )
            }
            <Button
              onClick={onCancel}
            >
              {t('operation.cancel', { ns: 'common' })}
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={isLoading || doingAction || !canSaveCredentialChange}
            >
              {saveButtonText}
            </Button>
          </div>
        </div>
        {
          (mode === ModelModalModeEnum.configCustomModel || mode === ModelModalModeEnum.configProviderCredential) && (
            <div className="shrink-0 border-t-[0.5px] border-t-divider-regular">
              <div className="flex items-center justify-center rounded-b-2xl bg-background-section-burn py-3 text-xs text-text-tertiary">
                <Lock01 className="mr-1 size-3 text-text-tertiary" />
                {t('modelProvider.encrypted.front', { ns: 'common' })}
                <a
                  className="mx-1 text-text-accent"
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://pycryptodome.readthedocs.io/en/latest/src/cipher/oaep.html"
                >
                  PKCS1_OAEP
                </a>
                {t('modelProvider.encrypted.back', { ns: 'common' })}
              </div>
            </div>
          )
        }
      </DialogContent>
      <AlertDialog open={!!deleteCredentialId} onOpenChange={handleConfirmOpenChange}>
        <AlertDialogContent backdropProps={{ forceRender: true }}>
          <div className="flex flex-col gap-2 p-6 pb-4">
            <AlertDialogTitle className="title-2xl-semi-bold text-text-primary">
              {t('modelProvider.confirmDelete', { ns: 'common' })}
            </AlertDialogTitle>
          </div>
          <AlertDialogActions>
            <AlertDialogCancelButton>{t('operation.cancel', { ns: 'common' })}</AlertDialogCancelButton>
            <AlertDialogConfirmButton
              disabled={doingAction}
              onClick={handleDeleteCredential}
            >
              {t('operation.confirm', { ns: 'common' })}
            </AlertDialogConfirmButton>
          </AlertDialogActions>
        </AlertDialogContent>
      </AlertDialog>
    </Dialog>
  )
}

export default memo(ModelModal)
