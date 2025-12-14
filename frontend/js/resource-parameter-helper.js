// Resource parameter helper for detecting resource types and parameter requirements
// Ported from cockpit-ext

const RESOURCE_PARAMETER_HELPER = {
    // Detect resource type and return parameter configuration
    getResourceParameterConfig: function(catalogEntry) {
        if (!catalogEntry) {
            return this.getDefaultConfig();
        }

        const type = catalogEntry.Type || '';
        const category = catalogEntry.Category || '';
        const operation = catalogEntry.Operation || '';
        const flags = catalogEntry.Flags || '';

        // Synthetic Virtual Machine entry (VM:{generation})
        if (type.startsWith('VM:')) {
            const generationMatch = type.match(/VM:(v\d+)/);
            const generation = generationMatch ? generationMatch[1] : null;
            
            return {
                type: 'vm-synthetic',
                parameters: [
                    {
                        name: 'cpuPerformance',
                        label: 'CPU Performance',
                        type: 'select',
                        required: true,
                        value: 'medium',
                        options: [
                            { value: 'medium', label: 'Medium' },
                            { value: 'high', label: 'High' },
                            { value: 'highest', label: 'Highest' }
                        ],
                        helpText: 'Select the CPU performance level'
                    },
                    {
                        name: 'vCores',
                        label: 'Number of vCores',
                        type: 'number',
                        required: true,
                        min: 1,
                        max: 256,
                        step: 1,
                        value: 1,
                        unit: 'vCores',
                        helpText: 'Number of virtual CPU cores'
                    },
                    {
                        name: 'ram',
                        label: 'RAM',
                        type: 'number',
                        required: true,
                        min: 1,
                        max: 1024,
                        step: 1,
                        value: 4,
                        unit: 'GiB',
                        helpText: 'Amount of RAM in GiB'
                    }
                ],
                displayName: 'Virtual Machine',
                generation: generation
            };
        }

        // Virtual Machine - vCores (legacy support for direct CustomCore selection)
        if (type.startsWith('CustomCore:')) {
            // Extract generation from type (e.g., "CustomCore:v4-p1" -> "v4")
            const generationMatch = type.match(/CustomCore:(v\d+)/);
            const generation = generationMatch ? generationMatch[1] : null;
            
            return {
                type: 'vm-vcore',
                parameters: [
                    {
                        name: 'cpuGeneration',
                        label: 'CPU Generation',
                        type: 'select',
                        required: true,
                        value: generation || 'v4',
                        options: this.getAvailableGenerations(catalogEntry),
                        helpText: 'Select the CPU generation for the virtual machine'
                    },
                    {
                        name: 'vCores',
                        label: 'Number of vCores',
                        type: 'number',
                        required: true,
                        min: 1,
                        max: 256,
                        step: 1,
                        value: 1,
                        unit: 'vCores',
                        helpText: 'Number of virtual CPU cores'
                    }
                ],
                displayName: 'Virtual Machine (vCores)',
                groupWith: ['vm-ram']
            };
        }

        // Virtual Machine - RAM
        if (type === 'CustomRam') {
            return {
                type: 'vm-ram',
                parameters: [
                    {
                        name: 'ram',
                        label: 'RAM',
                        type: 'number',
                        required: true,
                        min: 1,
                        max: 1024,
                        step: 1,
                        value: 4,
                        unit: 'GiB',
                        helpText: 'Amount of RAM in GiB'
                    }
                ],
                displayName: 'Virtual Machine (RAM)',
                groupWith: ['vm-vcore']
            };
        }

        // Block Storage - Volume Size
        if (type.startsWith('BSU:VolumeUsage:')) {
            const storageType = type.split(':')[2] || 'standard';
            const parameters = [
                {
                    name: 'size',
                    label: 'Volume Size',
                    type: 'number',
                    required: true,
                    min: 1,
                    max: 16384,
                    step: 1,
                    value: 100,
                    unit: 'GiB',
                    helpText: `Volume size in GiB (${storageType} storage)`,
                    isMonthly: flags.includes('PER_MONTH')
                }
            ];

            // For io1 storage type, add IOPS parameter
            if (storageType === 'io1') {
                parameters.push({
                    name: 'iops',
                    label: 'Provisioned IOPS',
                    type: 'number',
                    required: true,
                    min: 100,
                    max: 32000,
                    step: 100,
                    value: 3000,
                    unit: 'IOPS',
                    helpText: 'Number of provisioned IOPS for io1 storage (100-32000)',
                    isMonthly: flags.includes('PER_MONTH')
                });
            }

            return {
                type: 'storage-volume',
                parameters: parameters,
                displayName: `Block Storage (${storageType})`,
                storageType: storageType,
                hasIOPS: storageType === 'io1'
            };
        }

        // Block Storage - IOPS
        if (type === 'BSU:VolumeIOPS:io1') {
            return {
                type: 'storage-iops',
                parameters: [
                    {
                        name: 'iops',
                        label: 'IOPS',
                        type: 'number',
                        required: true,
                        min: 100,
                        max: 32000,
                        step: 100,
                        value: 3000,
                        unit: 'IOPS',
                        helpText: 'Number of IOPS for io1 storage volume',
                        isMonthly: flags.includes('PER_MONTH')
                    }
                ],
                displayName: 'Block Storage (IOPS)',
                groupWith: ['storage-volume']
            };
        }

        // Snapshots
        if (type === 'Snapshot:Usage') {
            return {
                type: 'storage-snapshot',
                parameters: [
                    {
                        name: 'size',
                        label: 'Snapshot Size',
                        type: 'number',
                        required: true,
                        min: 1,
                        max: 16384,
                        step: 1,
                        value: 100,
                        unit: 'GiB',
                        helpText: 'Snapshot size in GiB',
                        isMonthly: flags.includes('PER_MONTH')
                    }
                ],
                displayName: 'Snapshot Storage'
            };
        }

        // GPU
        if (type.startsWith('Gpu:')) {
            return {
                type: 'gpu',
                parameters: [
                    {
                        name: 'quantity',
                        label: 'Number of GPUs',
                        type: 'number',
                        required: true,
                        min: 1,
                        max: 16,
                        step: 1,
                        value: 1,
                        unit: 'GPUs',
                        helpText: 'Number of GPU instances'
                    }
                ],
                displayName: 'GPU'
            };
        }

        // Default configuration
        return this.getDefaultConfig();
    },

    // Get default parameter configuration
    getDefaultConfig: function() {
        return {
            type: 'default',
            parameters: [
                {
                    name: 'quantity',
                    label: 'Quantity',
                    type: 'number',
                    required: true,
                    min: 1,
                    max: 1000,
                    step: 1,
                    value: 1,
                    unit: '',
                    helpText: 'Quantity of this resource'
                }
            ],
            displayName: 'Resource'
        };
    },

    // Extract available CPU generations from catalog entries
    getAvailableGenerations: function(currentEntry) {
        // This will be populated dynamically from the catalog
        // For now, return common generations
        return [
            { value: 'v1', label: 'v1' },
            { value: 'v2', label: 'v2' },
            { value: 'v3', label: 'v3' },
            { value: 'v4', label: 'v4' },
            { value: 'v5', label: 'v5' },
            { value: 'v6', label: 'v6' },
            { value: 'v7', label: 'v7' },
            { value: 'v104', label: 'v104' }
        ];
    },

    // Get available generations from catalog
    getGenerationsFromCatalog: function(catalog) {
        const generations = new Set();
        
        // Use CATALOG_SERVICE if available, otherwise parse directly
        let entries = [];
        if (typeof CATALOG_SERVICE !== 'undefined' && CATALOG_SERVICE.parseResources) {
            entries = CATALOG_SERVICE.parseResources(catalog) || [];
        } else if (catalog && catalog.Catalog && catalog.Catalog.Entries) {
            entries = catalog.Catalog.Entries;
        } else if (Array.isArray(catalog)) {
            entries = catalog;
        }
        
        entries.forEach(entry => {
            if (entry.Type && entry.Type.startsWith('CustomCore:')) {
                const match = entry.Type.match(/CustomCore:(v\d+)/);
                if (match) {
                    generations.add(match[1]);
                }
            }
        });

        return Array.from(generations).sort().map(gen => ({
            value: gen,
            label: gen.toUpperCase()
        }));
    },

    // Extract generation from CustomCore type
    extractGeneration: function(type) {
        const match = type ? type.match(/CustomCore:(v\d+)/) : null;
        return match ? match[1] : null;
    },

    // Filter catalog entries by generation
    filterByGeneration: function(entries, generation) {
        if (!generation) return entries;
        return entries.filter(entry => {
            const entryGen = this.extractGeneration(entry.Type);
            return entryGen === generation;
        });
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RESOURCE_PARAMETER_HELPER;
}

