import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Icon } from '@/components/atoms/Icon'
import { Divider } from '@/components/atoms/Divider'
import { Tab } from '@/components/atoms/Tab'

export interface TabBarItem<T extends string = string> {
  id: T
  label: string
  icon?: string
}

export interface TabBarProps<T extends string = string> {
  items: TabBarItem<T>[]
  activeId: T
  onChange: (id: T) => void
  className?: string
}

/**
 * Molecule TabBar : navigation par onglets generique.
 *
 * Reutilisable par toute page ou organisme ayant besoin d onglets.
 * L identifiant d onglet est generique (`T extends string`) pour conserver
 * le typage des unions cote appelant.
 */
export const TabBar = <T extends string>({
  items,
  activeId,
  onChange,
  className,
}: TabBarProps<T>) => {
  return (
    <Box className={className}>
      <Stack spacing="xs">
        <Flex gap="none" className="border-b border-border">
          {items.map((item) => (
            <Tab
              key={item.id}
              isActive={activeId === item.id}
              onClick={() => onChange(item.id)}
              className="border-b-2 px-6 py-4"
            >
              <Flex align="center" gap="xs">
                {item.icon && <Icon name={item.icon} size="sm" aria-hidden />}
                <Text size="sm" weight="medium">
                  {item.label}
                </Text>
              </Flex>
            </Tab>
          ))}
        </Flex>
        <Divider />
      </Stack>
    </Box>
  )
}

export default TabBar
