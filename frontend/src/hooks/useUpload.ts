import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { uploadPortfolio, uploadComments, uploadGrowthData, fetchUploadHistory } from '../api/upload'

export function useUploadPortfolio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: uploadPortfolio,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['companies'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
      qc.invalidateQueries({ queryKey: ['upload-history'] })
    },
  })
}

export function useUploadComments() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: uploadComments,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['companies'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
      qc.invalidateQueries({ queryKey: ['upload-history'] })
    },
  })
}

export function useUploadGrowthData() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: uploadGrowthData,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['companies'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
      qc.invalidateQueries({ queryKey: ['upload-history'] })
    },
  })
}

export function useUploadHistory() {
  return useQuery({
    queryKey: ['upload-history'],
    queryFn: fetchUploadHistory,
  })
}
