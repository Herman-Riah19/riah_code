import type React from 'react'
import { Flex, type FlexProps } from '../Flex'

export interface StackProps extends Omit<FlexProps, 'direction' | 'gap'> {
  direction?: 'vertical' | 'horizontal'
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}

export const Stack: React.FC<StackProps> = ({
  direction = 'vertical',
  spacing = 'md',
  ...rest
}) => (
  <Flex
    direction={direction === 'vertical' ? 'column' : 'row'}
    gap={spacing}
    {...rest}
  />
)
