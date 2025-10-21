import { readFileSync } from 'node:fs'
import path from 'node:path'

interface MockDefinition {
  pattern: string
  method?: string
  body: unknown
  status?: number
}

const repoRoot = path.resolve(process.cwd(), '..')

const tagHierarchyFixturePath = path.resolve(
  repoRoot,
  'genonaut/ontologies/tags/data/hierarchy.json'
)

const tagHierarchyFixture = JSON.parse(readFileSync(tagHierarchyFixturePath, 'utf-8'))

const nowIso = new Date().toISOString()

const mockUser = {
  id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
  name: 'Admin User',
  email: 'admin@example.test',
  is_active: true,
  avatar_url: null,
  created_at: nowIso,
  updated_at: nowIso,
}

const mockGalleryResponse = {
  items: [
    {
      id: 1,
      title: 'Mock Artwork',
      description: 'Placeholder content for gallery tests.',
      image_url: null,
      content_type: 'image',
      content_data: '/static/mock/fullsize.png',
      path_thumb: '/static/mock/thumb.png',
      quality_score: 0.82,
      created_at: nowIso,
      updated_at: nowIso,
      creator_id: mockUser.id,
      source_type: 'regular',
      item_metadata: { prompt: 'A serene landscape' },
      tags: ['artistic_medium'],
      is_private: false,
      is_public: true,
    },
  ],
  pagination: {
    page: 1,
    page_size: 25,
    total_count: 1,
    total_pages: 1,
    has_next: false,
    has_previous: false,
  },
  stats: {
    user_regular_count: 1,
    user_auto_count: 0,
    community_regular_count: 0,
    community_auto_count: 0,
  },
}

const mockContentListResponse = {
  items: [
    {
      id: 1,
      title: 'Mock Artwork',
      description: 'Placeholder content for gallery tests.',
      image_url: null,
      content_type: 'image',
      content_data: '/static/mock/fullsize.png',
      path_thumb: '/static/mock/thumb.png',
      quality_score: 0.82,
      created_at: nowIso,
      updated_at: nowIso,
      creator_id: mockUser.id,
      item_metadata: { prompt: 'A serene landscape' },
      tags: ['artistic_medium'],
      is_private: false,
      is_public: true,
    },
    {
      id: 2,
      title: 'Community Item',
      description: 'Community generated content.',
      image_url: null,
      content_type: 'image',
      content_data: '/static/mock/community.png',
      path_thumb: '/static/mock/community-thumb.png',
      quality_score: 0.74,
      created_at: nowIso,
      updated_at: nowIso,
      creator_id: 'community-user',
      item_metadata: { prompt: 'Community artwork' },
      tags: ['community'],
      is_private: false,
      is_public: true,
    },
  ],
  total: 2,
  limit: 5,
  skip: 0,
}

const mockContentAutoListResponse = {
  items: [
    {
      id: 3,
      title: 'Auto Generated Item',
      description: 'Auto generated placeholder.',
      image_url: null,
      content_type: 'image',
      content_data: '/static/mock/auto.png',
      path_thumb: '/static/mock/auto-thumb.png',
      quality_score: 0.7,
      created_at: nowIso,
      updated_at: nowIso,
      creator_id: mockUser.id,
      item_metadata: { prompt: 'Auto generated prompt' },
      tags: ['auto'],
      is_private: false,
      is_public: true,
    },
  ],
  total: 1,
  limit: 5,
  skip: 0,
}

export function getCommonApiMocks(): MockDefinition[] {
  return [
    {
      pattern: '/api/v1/users/.*',
      method: 'GET',
      body: mockUser,
    },
    {
      pattern: '/api/v1/content/unified',
      method: 'GET',
      body: mockGalleryResponse,
    },
    {
      pattern: '/api/v1/content/\\d+$',
      method: 'GET',
      body: cloneDeep(mockGalleryResponse.items[0]),
    },
    {
      pattern: '/api/v1/content\\?.*',
      method: 'GET',
      body: cloneDeep(mockContentListResponse),
    },
    {
      pattern: '/api/v1/content-auto\\?.*',
      method: 'GET',
      body: cloneDeep(mockContentAutoListResponse),
    },
  ]
}

export function getTagHierarchyMocks(): MockDefinition[] {
  // Build tags list from hierarchy fixture
  const tags = tagHierarchyFixture.nodes.map((tag: any) => ({
    id: tag.id,
    name: tag.name,
    created_at: nowIso,
    updated_at: nowIso,
    metadata: {},
    average_rating: null,
    rating_count: 0,
    slug: tag.id,
    description: '',
    ancestors: [],
    descendants: [],
    is_favorite: false,
  }))

  return [
    {
      pattern: '/api/v1/tags/hierarchy',
      method: 'GET',
      body: cloneDeep(tagHierarchyFixture),
    },
    {
      pattern: '/api/v1/tags/hierarchy/refresh',
      method: 'POST',
      body: {
        message: 'Hierarchy refreshed',
        metadata: cloneDeep(tagHierarchyFixture.metadata),
      },
    },
    {
      pattern: '/api/v1/tags\\?.*',
      method: 'GET',
      body: {
        items: cloneDeep(tags),
        pagination: {
          page: 1,
          page_size: 100,
          total_count: tags.length,
          total_pages: 1,
        },
      },
    },
  ]
}

export function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}
