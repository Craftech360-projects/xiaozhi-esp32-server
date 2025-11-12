package xiaozhi.modules.content.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.content.dto.ContentItemsDTO;
import xiaozhi.modules.content.dto.ContentItemsSearchDTO;

/**
 * Content Items Service Interface
 */
public interface ContentItemsService {

    String createContentItem(ContentItemsDTO dto);

    Integer batchCreateContentItems(List<ContentItemsDTO> dtos);

    PageData<ContentItemsDTO> getContentItemsList(ContentItemsSearchDTO searchDTO);

    ContentItemsDTO getContentItemById(String id);

    List<ContentItemsDTO> getContentItemsByType(String contentType);

    List<ContentItemsDTO> getContentItemsByCategory(String category);

    PageData<ContentItemsDTO> searchContentItems(ContentItemsSearchDTO searchDTO);

    List<String> getCategoriesByType(String contentType);

    Map<String, Object> getStatistics();

    Boolean updateContentItem(String id, ContentItemsDTO dto);

    Boolean partialUpdateContentItem(String id, Map<String, Object> updates);

    Integer batchUpdateContentItems(List<ContentItemsDTO> dtos);

    Boolean deleteContentItem(String id);

    Integer batchDeleteContentItems(List<String> ids);
}
