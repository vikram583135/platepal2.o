import { Download } from 'lucide-react'

interface CSVExporterProps {
  data: Record<string, any>[]
  filename?: string
  className?: string
  onExportComplete?: () => void
}

export function CSVExporter({ data, filename = 'export.csv', className, onExportComplete }: CSVExporterProps) {
  const convertToCSV = (data: Record<string, any>[]): string => {
    if (data.length === 0) return ''

    const headers = Object.keys(data[0])
    const rows = data.map(row =>
      headers.map(header => {
        const value = row[header]
        if (value === null || value === undefined) return ''
        if (typeof value === 'object') return JSON.stringify(value)
        return String(value).replace(/"/g, '""')
      })
    )

    const csvContent = [
      headers.map(h => `"${h}"`).join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    return csvContent
  }

  const handleExport = () => {
    const csv = convertToCSV(data)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    if (onExportComplete) {
      onExportComplete()
    }
  }

  return (
    <button
      onClick={handleExport}
      className={`flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 ${className || ''}`}
    >
      <Download className="w-4 h-4" />
      Export CSV
    </button>
  )
}

