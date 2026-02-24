// This file simulates a database of authorized users for different health networks.

export type UserPermissionLevel = 'Básico' | 'Médio' | 'Administrativo';

export interface User {
  id: string;
  name: string;
  professionalId: string; // CRM, CRP, or Admin ID
  password: string; // In a real app, this would be a hash
  healthNetworkId: string; // Corresponds to the ID in the healthNetworks array
  permissionLevel: UserPermissionLevel;
}

export const users: User[] = [
  // Users for Hospital das Clínicas - SP
  {
    id: '101',
    name: 'Dr. Ana Oliveira',
    professionalId: '123456-SP',
    password: 'password123',
    healthNetworkId: 'hc_sp',
    permissionLevel: 'Básico',
  },
  {
    id: '102',
    name: 'Dr. Carlos Santos',
    professionalId: '789012-SP',
    password: 'password123',
    healthNetworkId: 'hc_sp',
    permissionLevel: 'Médio',
  },
  {
    id: '103',
    name: 'Gestor Silva',
    professionalId: 'ADM-HCSP-01',
    password: 'adminpass',
    healthNetworkId: 'hc_sp',
    permissionLevel: 'Administrativo',
  },

  // Users for Hospital Israelita Albert Einstein
  {
    id: '201',
    name: 'Dra. Beatriz Lima',
    professionalId: '112233-SP',
    password: 'password123',
    healthNetworkId: 'einstein',
    permissionLevel: 'Básico',
  },
  {
    id: '202',
    name: 'Gestora Costa',
    professionalId: 'ADM-EINSTEIN-01',
    password: 'adminpass',
    healthNetworkId: 'einstein',
    permissionLevel: 'Administrativo',
  },

  // Users for Rede Unimed
  {
    id: '301',
    name: 'Dr. Roberto Alves',
    professionalId: '445566-RJ',
    password: 'password123',
    healthNetworkId: 'unimed',
    permissionLevel: 'Médio',
  },

  // User for Hospital Sírio-Libanês (for user testing)
  {
    id: '401',
    name: 'Dr. Usuário Teste',
    professionalId: 'PRO-SL-2024',
    password: 'sirio123',
    healthNetworkId: 'sirio',
    permissionLevel: 'Médio',
  },
];
