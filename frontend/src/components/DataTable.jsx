
function DataTable({
  columns,
  data,
}) {
  if (!data || data.length === 0) {
    return null;
  }

  return (
    <div className="table-wrapper">

      <table className="data-table">

        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>

          {data.map((row, index) => (
            <tr key={index}>

              {columns.map((column) => (
                <td key={column.key}>

                  {column.render
                    ? column.render(row)
                    : row[column.key] ?? "—"}

                </td>
              ))}

            </tr>
          ))}

        </tbody>

      </table>

    </div>
  );
}

export default DataTable;