import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MdProps {
  children: string;
}

export const Md: React.FC<MdProps> = ({ children }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      table: ({ children }) => (
        <table
          style={{ width: "100%", borderCollapse: "collapse", margin: "8px 0" }}
        >
          {children}
        </table>
      ),
      th: ({ children, style, ...rest }) => (
        <th
          style={{
            border: "1px solid #ddd",
            padding: "8px",
            backgroundColor: "#f5f5f5",
            fontWeight: "600",
            ...style,
          }}
        >
          {children}
        </th>
      ),
      td: ({ children, style, ...rest }) => (
        <td
          style={{
            border: "1px solid #ddd",
            padding: "8px",
            ...style,
          }}
        >
          {children}
        </td>
      ),
    }}
  >
    {children}
  </ReactMarkdown>
);

export default Md;
