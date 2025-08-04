/**
 * Sample input data templates for testing and demonstration purposes.
 * These templates provide realistic data for different security analysis scenarios.
 */

export interface InputTemplate {
  label: string;
  data: Record<string, any>;
}

export const INPUT_TEMPLATES: Record<string, InputTemplate> = {
  host_analysis: {
    label: "Host Analysis",
    data: {
      ip: "8.8.8.8",
      domain: "dns.google",
      os: "linux",
      ports: [53, 443, 853],
      services: ["dns", "https"],
    },
  },
  certificate_scan: {
    label: "Certificate Scan",
    data: {
      domain: "example.com",
      ip: "93.184.216.34",
      port: 443,
      protocol: "https",
    },
  },
  vulnerability_check: {
    label: "Vulnerability Check",
    data: {
      ip: "192.168.1.100",
      os: "ubuntu-20.04",
      services: ["apache/2.4.41", "mysql/8.0.25"],
      software: ["nodejs/14.17.0", "nginx/1.18.0"],
    },
  },
};

export default INPUT_TEMPLATES;
