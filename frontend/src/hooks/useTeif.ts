import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { teifService } from '../services/teifService';
import { useToast } from '@chakra-ui/react';

export const useTeif = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const toast = useToast();

  const generateTeifMutation = useMutation({
    mutationFn: async (invoiceId: number) => {
      setIsGenerating(true);
      try {
        return await teifService.generateTeif(invoiceId);
      } finally {
        setIsGenerating(false);
      }
    },
    onSuccess: (data, invoiceId) => {
      // Télécharger le fichier généré
      const blob = new Blob([data], { type: 'application/xml' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice_${invoiceId}_${new Date().toISOString().split('T')[0]}.xml`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Succès',
        description: 'Le fichier TEIF a été généré avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    },
    onError: (error: Error) => {
      console.error('Erreur lors de la génération du TEIF:', error);
      toast({
        title: 'Erreur',
        description: 'Une erreur est survenue lors de la génération du fichier TEIF',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  });

  return {
    generateTeif: generateTeifMutation.mutate,
    isGenerating,
  };
};