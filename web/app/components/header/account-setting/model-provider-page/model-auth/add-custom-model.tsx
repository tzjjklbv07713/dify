import type {
  ConfigurationMethodEnum,
  CustomConfigurationModelFixedFields,
  ModelProvider,
} from '@/app/components/header/account-setting/model-provider-page/declarations'
import {
  Button,
} from '@langgenius/dify-ui/button'
import { cn } from '@langgenius/dify-ui/cn'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@langgenius/dify-ui/popover'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@langgenius/dify-ui/tooltip'
import {
  memo,
  useCallback,
  useMemo,
  useState,
} from 'react'
import { useTranslation } from 'react-i18next'
import { ModelModalModeEnum } from '@/app/components/header/account-setting/model-provider-page/declarations'
import { useCredentialPermissions } from '@/hooks/use-credential-permissions'
import ModelIcon from '../model-icon'
import { useAuth } from './hooks/use-auth'
import { useCanAddedModels } from './hooks/use-custom-models'

type AddCustomModelProps = {
  provider: ModelProvider
  configurationMethod: ConfigurationMethodEnum
  currentCustomConfigurationModelFixedFields?: CustomConfigurationModelFixedFields
  open?: boolean
  onOpenChange?: (open: boolean) => void
}
const AddCustomModel = ({
  provider,
  configurationMethod,
  currentCustomConfigurationModelFixedFields,
}: AddCustomModelProps) => {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const canAddedModels = useCanAddedModels(provider)
  const noModels = !canAddedModels.length
  const supportsModelDiscovery = useMemo(() => {
    const variables = new Set((provider.model_credential_schema?.credential_form_schemas || []).map(schema => schema.variable))
    const hasBaseUrl = variables.has('proxy_base_url') || variables.has('endpoint_url')
    const hasApiKey = variables.has('proxy_api_key') || variables.has('api_key') || variables.has('openai_api_key')
    return hasBaseUrl && hasApiKey
  }, [provider.model_credential_schema])
  const { canUseCredential, canCreateCredential } = useCredentialPermissions()
  const {
    handleOpenModal: handleOpenModalForAddNewCustomModel,
  } = useAuth(
    provider,
    configurationMethod,
    currentCustomConfigurationModelFixedFields,
    {
      isModelCredential: true,
      mode: ModelModalModeEnum.configCustomModel,
    },
  )
  const {
    handleOpenModal: handleOpenModalForAddCustomModelToModelList,
  } = useAuth(
    provider,
    configurationMethod,
    currentCustomConfigurationModelFixedFields,
    {
      isModelCredential: true,
      mode: ModelModalModeEnum.addCustomModelToModelList,
    },
  )
  const notAllowCustomCredential = provider.allow_custom_token === false
  const renderTrigger = useCallback((open?: boolean, onClick?: () => void) => {
    const disabled = supportsModelDiscovery
      ? !canCreateCredential
      : noModels
        ? !canCreateCredential
        : !canUseCredential && !canCreateCredential
    const item = (
      <Button
        variant="ghost"
        size="small"
        onClick={onClick}
        className={cn(
          'text-text-tertiary',
          open && 'bg-components-button-ghost-bg-hover',
          notAllowCustomCredential && !!noModels && 'cursor-not-allowed opacity-50',
          disabled && 'cursor-not-allowed opacity-50',
        )}
      >
        <span className="i-ri-add-circle-fill mr-1 size-3.5" />
        {t('modelProvider.addModel', { ns: 'common' })}
      </Button>
    )
    if ((notAllowCustomCredential && !!noModels) || disabled) {
      return (
        <Tooltip>
          <TooltipTrigger render={item} />
          <TooltipContent>{t('auth.credentialUnavailable', { ns: 'plugin' })}</TooltipContent>
        </Tooltip>
      )
    }
    return item
  }, [canCreateCredential, canUseCredential, t, notAllowCustomCredential, noModels, supportsModelDiscovery])

  if (supportsModelDiscovery) {
    return renderTrigger(
      false,
      notAllowCustomCredential || !canCreateCredential ? undefined : handleOpenModalForAddNewCustomModel,
    )
  }

  if (noModels) {
    return renderTrigger(false, notAllowCustomCredential || !canCreateCredential ? undefined : handleOpenModalForAddNewCustomModel)
  }

  return (
    <Popover
      open={open}
      onOpenChange={setOpen}
    >
      <PopoverTrigger
        nativeButton={false}
        render={<div className="inline-block">{renderTrigger(open)}</div>}
      />
      <PopoverContent
        placement="bottom-end"
        sideOffset={4}
        popupClassName="border-0 bg-transparent p-0 shadow-none backdrop-blur-none"
      >
        <div className="w-[320px] rounded-xl border-[0.5px] border-components-panel-border bg-components-panel-bg-blur shadow-lg">
          <div className="max-h-[304px] overflow-y-auto p-1">
            {
              canAddedModels.map(model => (
                <div
                  key={model.model}
                  className={cn(
                    'flex h-8 items-center rounded-lg px-2',
                    canUseCredential ? 'cursor-pointer hover:bg-state-base-hover' : 'cursor-not-allowed opacity-50',
                  )}
                  aria-disabled={!canUseCredential}
                  onClick={() => {
                    if (!canUseCredential)
                      return

                    setOpen(false)
                    handleOpenModalForAddCustomModelToModelList(undefined, model)
                  }}
                >
                  <ModelIcon
                    className="mr-1 size-5 shrink-0"
                    iconClassName="h-5 w-5"
                    provider={provider}
                    modelName={model.model}
                  />
                  <div
                    className="grow truncate system-md-regular text-text-primary"
                    title={model.model}
                  >
                    {model.model}
                  </div>
                </div>
              ))
            }
          </div>
          {
            !notAllowCustomCredential && canCreateCredential && (
              <div
                className="flex cursor-pointer items-center border-t border-t-divider-subtle p-3 system-xs-medium text-text-accent-light-mode-only"
                onClick={() => {
                  setOpen(false)
                  handleOpenModalForAddNewCustomModel()
                }}
              >
                <span className="i-ri-add-line mr-1 size-4" />
                {t('modelProvider.auth.addNewModel', { ns: 'common' })}
              </div>
            )
          }
        </div>
      </PopoverContent>
    </Popover>
  )
}

export default memo(AddCustomModel)
