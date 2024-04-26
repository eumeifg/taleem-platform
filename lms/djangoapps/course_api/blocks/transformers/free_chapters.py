
from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer

class FreeChapterTransformer(BlockStructureTransformer):
    """
    Changes the transformer data structure and addig a flag in 
    all blocks with boolean value in order to restrict the access
    """

    READ_VERSION = 1
    WRITE_VERSION = 1
    HAS_ACCESS = 'has_access'

    @classmethod
    def name(cls):
        return "blocks_api:freechapters"

    def get_free_chapters(self,blocks,block_structure):
        sections_list = []
        subsequent_blocks = []
        for block_key in blocks:
            block_type = block_structure.get_xblock_field(block_key, 'category')
            if block_type == 'chapter':
                sections_list.append(block_key)

        for section_id in sections_list[3:]:
            subsequent_blocks.append(section_id)
            for sub_section_id in block_structure.get_children(section_id):
                subsequent_blocks.append(sub_section_id)
                for unit in block_structure.get_children(sub_section_id):
                    subsequent_blocks.append(unit)
                    for component in block_structure.get_children(unit):
                        subsequent_blocks.append(component)

        return subsequent_blocks

    def restrict_access(self,blocks,block_structure):
        """
        Helper function to make the flag false in the subsequent blocks so those
        will be unclickable in android application.

        :blocks all the block ids list including all the children
        :param block_structure: A BlockStructureBlockData object
        # """
        for block_key in blocks:
            block_structure.set_transformer_block_field(
                block_key,
                self,
                self.HAS_ACCESS,
                False
            )

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure adding one extra fields which contains has_access,a boolean flag
        to restrict the acces in mobile application 
        """
        
        blocks = []
        for block_key in block_structure.post_order_traversal():
            blocks.append(block_key)
        
        subsequent_blocks = self.get_free_chapters(blocks, block_structure)
        self.restrict_access(subsequent_blocks, block_structure)
