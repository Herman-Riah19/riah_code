import type React from 'react'

export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  children?: React.ReactNode
  className?: string
}

export const Table: React.FC<TableProps> = ({ className, ...rest }) => {
  return (
    <table
      className={[
        'w-full text-sm caption-medium rounded-lg border border-border',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    />
  )
}

export interface TableHeaderProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children?: React.ReactNode
  className?: string
}

export const TableHeader: React.FC<TableHeaderProps> = ({ className, ...rest }) => {
  return (
    <thead className={['bg-muted', className].filter(Boolean).join(' ')} {...rest} />
  )
}

export interface TableBodyProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children?: React.ReactNode
  className?: string
}

export const TableBody: React.FC<TableBodyProps> = ({ className, ...rest }) => {
  return <tbody className={['bg-background', className].filter(Boolean).join(' ')} {...rest} />
}

export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  children?: React.ReactNode
  className?: string
}

export const TableRow: React.FC<TableRowProps> = ({ className, ...rest }) => {
  return (
    <tr
      className={[
        'border-b border-border transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    />
  )
}

export interface TableHeadProps extends React.HTMLAttributes<HTMLTableCellElement> {
  children?: React.ReactNode
  className?: string
}

export const TableHead: React.FC<TableHeadProps> = ({ className, ...rest }) => {
  return (
    <th
      className={[
        'px-4 py-3 font-medium text-muted-foreground text-left',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    />
  )
}

export interface TableCellProps extends React.HTMLAttributes<HTMLTableCellElement> {
  children?: React.ReactNode
  className?: string
  colSpan?: number
}

export const TableCell: React.FC<TableCellProps> = ({ className, ...rest }) => {
  return (
    <td
      className={['px-4 py-3', className].filter(Boolean).join(' ')}
      {...rest}
    />
  )
}

export interface TableCaptionProps extends React.HTMLAttributes<HTMLTableCaptionElement> {
  children?: React.ReactNode
  className?: string
}

export const TableCaption: React.FC<TableCaptionProps> = ({ className, ...rest }) => {
  return (
    <caption
      className={['pb-4 font-medium text-muted-foreground text-left', className].filter(Boolean).join(' ')}
      {...rest}
    />
  )
}
