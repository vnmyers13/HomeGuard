import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import DataTable from '../../../src/components/DataTable'

describe('DataTable', () => {
  const columns = [
    { key: 'name', header: 'Name', sortable: true },
    { key: 'status', header: 'Status', sortable: true },
  ]

  const data = [
    { id: 1, name: 'Alice', status: 'active' },
    { id: 2, name: 'Bob', status: 'inactive' },
    { id: 3, name: 'Charlie', status: 'active' },
  ]

  it('renders table with data', () => {
    render(<DataTable columns={columns} data={data} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText('Charlie')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(<DataTable columns={columns} data={data} loading={true} />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('shows empty message when no data', () => {
    render(<DataTable columns={columns} data={[]} emptyMessage="No results" />)
    expect(screen.getByText('No results')).toBeInTheDocument()
  })

  it('handles search filtering', () => {
    render(<DataTable columns={columns} data={data} filterable={true} />)
    const searchInput = document.querySelector('input[type="text"]')
    fireEvent.change(searchInput, { target: { value: 'Alice' } })
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.queryByText('Bob')).not.toBeInTheDocument()
  })

  it('shows pagination info', () => {
    render(<DataTable columns={columns} data={data} />)
    expect(screen.getByText('Showing 1 to 3 of 3 results')).toBeInTheDocument()
  })

  it('renders per-page selector', () => {
    render(<DataTable columns={columns} data={data} />)
    expect(screen.getByText('Rows:')).toBeInTheDocument()
  })

  it('handles custom column render', () => {
    const renderColumns = [
      { key: 'name', header: 'Name' },
      {
        key: 'status',
        header: 'Status',
        render: (val) => <span className={`status-${val}`}>{val}</span>,
      },
    ]
    render(<DataTable columns={renderColumns} data={data} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(document.querySelectorAll('.status-active').length).toBeGreaterThan(0)
  })

  it('renders actions column', () => {
    const actionColumns = [
      { key: 'name', header: 'Name' },
    ]
    render(
      <DataTable
        columns={actionColumns}
        data={data}
        actions={(row) => <button>Delete {row.name}</button>}
      />
    )
    expect(screen.getByText('Delete Alice')).toBeInTheDocument()
  })
})
