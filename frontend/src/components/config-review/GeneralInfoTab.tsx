import type { GeneralInformation } from '../../types/config';
import { Building2, Calendar, Cog, Zap, Wind, User, Mail, Phone, MapPin, FileText } from 'lucide-react';

interface GeneralInfoTabProps {
  generalInfo: GeneralInformation;
}

interface InfoItemProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  unit?: string;
}

function InfoItem({ icon, label, value, unit }: InfoItemProps) {
  return (
    <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
      <div className="flex-shrink-0 mt-1 text-primary-dark">{icon}</div>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <p className="text-lg font-semibold text-gray-900 break-words">
          {value}
          {unit && <span className="text-sm text-gray-600 ml-1">{unit}</span>}
        </p>
      </div>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h4 className="text-md font-bold text-gray-700 mb-3 mt-6 first:mt-0">{children}</h4>;
}

export function GeneralInfoTab({ generalInfo }: GeneralInfoTabProps) {
  return (
    <div className="space-y-6">
      {/* Informations du projet */}
      <div>
        <SectionTitle>Informations du projet</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {generalInfo.name && (
            <InfoItem
              icon={<FileText className="w-5 h-5" />}
              label="Nom du projet"
              value={generalInfo.name}
            />
          )}
          {generalInfo.description && (
            <InfoItem
              icon={<FileText className="w-5 h-5" />}
              label="Description"
              value={generalInfo.description}
            />
          )}
          {generalInfo.date_archive && (
            <InfoItem
              icon={<Calendar className="w-5 h-5" />}
              label="Date d'archivage"
              value={generalInfo.date_archive}
            />
          )}
        </div>
      </div>

      {/* Informations du parc */}
      <div>
        <SectionTitle>Informations du parc éolien</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <InfoItem
            icon={<Building2 className="w-5 h-5" />}
            label="Nom du parc"
            value={generalInfo.park_name || 'N/A'}
          />
          {generalInfo.number_wtg && (
            <InfoItem
              icon={<Wind className="w-5 h-5" />}
              label="Nombre d'éoliennes"
              value={generalInfo.number_wtg}
            />
          )}
          {generalInfo.model_wtg && (
            <InfoItem
              icon={<Cog className="w-5 h-5" />}
              label="Modèle d'éolienne"
              value={generalInfo.model_wtg}
            />
          )}
          {generalInfo.nominal_power && (
            <InfoItem
              icon={<Zap className="w-5 h-5" />}
              label="Puissance nominale"
              value={generalInfo.nominal_power}
            />
          )}
          {generalInfo.v_rated && (
            <InfoItem
              icon={<Wind className="w-5 h-5" />}
              label="Vitesse nominale"
              value={generalInfo.v_rated}
              unit="m/s"
            />
          )}
          {generalInfo.constructor && (
            <InfoItem
              icon={<Building2 className="w-5 h-5" />}
              label="Constructeur"
              value={generalInfo.constructor}
            />
          )}
        </div>
      </div>

      {/* Informations client */}
      {(generalInfo.client_name || generalInfo.client_location || generalInfo.client_contact) && (
        <div>
          <SectionTitle>Informations client</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {generalInfo.client_name && (
              <InfoItem
                icon={<Building2 className="w-5 h-5" />}
                label="Client"
                value={generalInfo.client_name}
              />
            )}
            {generalInfo.client_location && (
              <InfoItem
                icon={<MapPin className="w-5 h-5" />}
                label="Localisation"
                value={generalInfo.client_location}
              />
            )}
            {generalInfo.client_contact && (
              <InfoItem
                icon={<Mail className="w-5 h-5" />}
                label="Contact"
                value={generalInfo.client_contact}
              />
            )}
          </div>
        </div>
      )}

      {/* Équipe */}
      {(generalInfo.author_name || generalInfo.writer_name || generalInfo.verificator_name) && (
        <div>
          <SectionTitle>Équipe du projet</SectionTitle>
          <div className="space-y-4">
            {/* Auteur */}
            {generalInfo.author_name && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-blue-900 mb-2">Auteur</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <User className="w-4 h-4 text-blue-600" />
                    <span>{generalInfo.author_name}</span>
                  </div>
                  {generalInfo.author_email && (
                    <div className="flex items-center space-x-2">
                      <Mail className="w-4 h-4 text-blue-600" />
                      <span className="break-all">{generalInfo.author_email}</span>
                    </div>
                  )}
                  {generalInfo.author_phone && (
                    <div className="flex items-center space-x-2">
                      <Phone className="w-4 h-4 text-blue-600" />
                      <span>{generalInfo.author_phone}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Rédacteur */}
            {generalInfo.writer_name && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-green-900 mb-2">Rédacteur</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <User className="w-4 h-4 text-green-600" />
                    <span>{generalInfo.writer_name}</span>
                  </div>
                  {generalInfo.writer_email && (
                    <div className="flex items-center space-x-2">
                      <Mail className="w-4 h-4 text-green-600" />
                      <span className="break-all">{generalInfo.writer_email}</span>
                    </div>
                  )}
                  {generalInfo.writer_phone && (
                    <div className="flex items-center space-x-2">
                      <Phone className="w-4 h-4 text-green-600" />
                      <span>{generalInfo.writer_phone}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Vérificateur */}
            {generalInfo.verificator_name && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-purple-900 mb-2">Vérificateur</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <User className="w-4 h-4 text-purple-600" />
                    <span>{generalInfo.verificator_name}</span>
                  </div>
                  {generalInfo.verficator_email && (
                    <div className="flex items-center space-x-2">
                      <Mail className="w-4 h-4 text-purple-600" />
                      <span className="break-all">{generalInfo.verficator_email}</span>
                    </div>
                  )}
                  {generalInfo.verficator_phone && (
                    <div className="flex items-center space-x-2">
                      <Phone className="w-4 h-4 text-purple-600" />
                      <span>{generalInfo.verficator_phone}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
