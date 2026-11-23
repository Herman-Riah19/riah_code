import type React from 'react'
import { Flex } from '@/components/atoms/Flex'
import { Tab } from '@/components/atoms/Tab'
import { Text } from '@/components/atoms/Text'

export interface ToggleOption {
  value: string
  label: string
}

export interface ToggleGroupProps {
  options: ToggleOption[]
  value: string[]
  onChange: (value: string[]) => void
  multiple?: boolean
  isDisabled?: boolean
  className?: string
}

export const ToggleGroup: React.FC<ToggleGroupProps> = ({
  options,
  value,
  onChange,
  multiple = false,
  isDisabled = false,
  className,
}) => {
  const handleToggle = (optionValue: string) => {
    if (isDisabled) return
    if (!multiple) {
      onChange([optionValue])
      return
    }
    onChange(
      value.includes(optionValue)
        ? value.filter((item) => item !== optionValue)
        : [...value, optionValue],
    )
  }

  return (
    <Flex wrap gap="sm" className={className}>
      {options.map((option) => {
        const isActive = value.includes(option.value)
        return (
          <Tab
            key={option.value}
            isActive={isActive}
            // disabled={isDisabled}
            aria-pressed={isActive}
            onClick={() => handleToggle(option.value)}
          >
            <Text
              as="span"
              size="sm"
              weight={isActive ? 'semibold' : 'normal'}
              color="default"
            >
              {option.label}
            </Text>
          </Tab>
        )
      })}
    </Flex>
  )
}
